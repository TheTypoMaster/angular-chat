# -*- coding: utf-8 -*-
"""
    Simple sockjs-tornado chat application. By default will listen on port 5555.
"""
import tornado.ioloop
import tornado.web
import time
import sockjs.tornado
import brukva
import json
import logging
from main.models import ChatUser, Tpa, ChatRoom, ChatUser2Room, ChatTransactions
from django.core.exceptions import ObjectDoesNotExist
c = brukva.Client()
c.connect()
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
from main.tasks import save_chat_message, manage_with_contacts, make_room_as_charging, remoute_deduct, set_user_offline, set_user_online
import main.utils as utils
import os
import md5
import pickle
from sets import Set
from main.utils import create_room_if_not_exists
from django.utils.translation import ugettext as _
from datetime import timedelta, datetime
import time

class ChatConnection(sockjs.tornado.SockJSConnection):
    """Chat connection implementation"""
    participants = set() # List of users online

    # Initialization
    def __init__(self,*args):
        super(ChatConnection, self).__init__(*args)
        self.client = brukva.Client()
        self.client.connect()
        self.is_auth = 'false' # Is current user obline?
        self.profile = 'none'
        self.tpa = None # Current users web-site, registered in chat system
        self.current_user = None # ChatUser object of current user
        self.connection = False # Is connection complete successfull?
        self.room = None # ChatRoom object of current room
        self.rooms = Set([]) # list of the ChatRoom objects of current user
        self.account = None # Balance in users account
        self.identifier = None # Current user identifier like OURSITEID_OURUSERID
        self.price_common = None # Money per minute current user must pay for common chat
        self.price_private = None # Money per minute current user must pay for private chat
        self.price_spy = None # Money per minute current user must pay for spy chat
        self.is_noticed_about_empty_account = False # Is user has money?
        self.place = 'chat' #plase tpa site or chat



    # When connection need to be open, first of all we go here
    # info ?????
    def on_open(self, info):
        ''' function when someone made connection from javascript'''
        # Send that someone joined
        message = {"act" : "someone_joined", "content" : "Someone joined"}
        self.broadcast(self.participants, json.dumps(message))
        # Add client to the clients list
        self.participants.add(self)

    # When we receive message from redis server we go here
    def redis_message(self, result):
        ''' recieving  message from redis server, 
            convertin it in json format 
            and sending it to the current chanel
        '''
        message = json.loads(result.body)
        self.send(json.dumps(message))

    # Subscribe user to channel
    def subscribe(self, room):
        self.client.subscribe(room) # Redis subscribe
        logger.debug('subscribing to room %s' % (room, )) # Debug
        self.client.listen(self.redis_message)

    # When we receive messages we go here
    def on_message(self, message):
        ''' handler of message '''
        
        logger.debug(message) # Debug
        message = json.loads(message)
        # When we open connection
        if message['act'] == 'open_connect':
            self.connection = self.get_connection_or_create(message)
            self.subscribe(self.get_connection_sign())
            if self.connection != False :
                print '%s_%s Connected!' % ( self.tpa.id, self.current_user.id )
                #send message to all people to add me online
                mes = json.dumps({ "gender":self.current_user.gender, "uid" : str(self.current_user.id), "act" : "add_me_to_online" })
                self.broadcast(self.participants, mes)
            else:
                print 'Fail connect!'
            try:
                if( message['room_type']=='common'):
                    mes = { "act" : "put_me_in_room", "room_id" : message['room_id']}
                    c.publish('%s_%s' % ( self.tpa.id, self.current_user.id ), json.dumps(mes))
                if( message['room_type']=='spy'):  
                    mes = { 'act': 'add_video_to_slot', 'uid': message['uid'] }
                    c.publish('%s_%s' % ( self.tpa.id, self.current_user.id ), json.dumps(mes))         
            except:
                pass
            

        # connection from tpa js script
        if message['act'] == 'tpa_connect':
            chanel = 'tpa_channel_%s_%s' % (message['tpa_id'], message['user_id'])
            print 'subscribe from tpa %s' % chanel
            self.subscribe(chanel)
            #ChatUser.objects.raw("update main_chatuser set is_online=1 where tpa_id=%s and id=%s" % (message['tpa_id'],message['user_id']))
            self.current_user = ChatUser.objects.get(id=message['user_id'])
            self.place = 'tpa'
            tpa = Tpa.objects.get(pk=message['tpa_id'])
            self.tpa = tpa
            set_user_online(self.current_user, self.tpa)
            ChatUser.objects.filter(tpa_id=message['tpa_id'], id=message['user_id']).update(is_online=1)
            #print "update main_chatuser set is_online=1 where tpa_id=%s and id=%s" % (message['tpa_id'],message['user_id'])
            online_users = ChatUser.objects.raw("select id, user_id from main_chatuser where tpa_id=%s and is_online=1" % message['tpa_id'])
            with_cam_users = ChatUser.objects.raw("select id, user_id from main_chatuser where tpa_id=%s and is_online=1 and is_camera_active=True" % message['tpa_id'])
            ou = []
            for u in online_users:
                #cupid24682476web-cupid 
                #define who connected
                if(int(message['remote_user_id']) != int(u.user_id)):
                    sign_str = '%s%s%s%s' % (tpa.name, message['remote_user_id'], u.user_id, tpa.secret)
                    sign_md5 = md5.new(sign_str).hexdigest()
                    sign_str_rev = '%s%s%s%s' % (tpa.name, u.user_id, message['remote_user_id'], tpa.secret)
                    sign_md5_rev = md5.new(sign_str_rev).hexdigest()
                    common_link = 'http://chat.%s/auth/common/%s/%s/%s/%s' % (tpa.domain, tpa.name, message['remote_user_id'], u.user_id, sign_md5)
                    common_reverse_link = 'http://chat.%s/auth/common/%s/%s/%s/%s' % (tpa.domain, tpa.name, u.user_id, message['remote_user_id'], sign_md5_rev)
                    watch_link = 'http://chat.%s/auth/spy/%s/%s/%s/%s' % (tpa.domain, tpa.name, message['remote_user_id'], u.user_id, sign_md5)
                    watch_reverse_link = 'http://chat.%s/auth/spy/%s/%s/%s/%s' % (tpa.domain, tpa.name, u.user_id, message['remote_user_id'], sign_md5_rev)
                    if(u.is_camera_active==True):
                        is_camera_active = 'yes'
                    else:
                        is_camera_active = 'no'
                    ou.append({ 'user_id': u.user_id, 
                                'common_link': common_link, 
                                'common_reverse_link': common_reverse_link, 
                                'watch_link': watch_link, 
                                'watch_reverse_link': watch_reverse_link, 
                                'is_camera_active': is_camera_active,
                                'remote_user_id': message['remote_user_id']
                                })
            camu = []
            for u in with_cam_users:
                #cupid24682476web-cupid 
                sign_str = '%s%s%s%s' % (tpa.name, message['remote_user_id'], u.user_id, tpa.secret)
                sign_md5 = md5.new(sign_str).hexdigest()
                link = 'http://chat.%s/auth/spy/%s/%s/%s/%s' % (tpa.domain, tpa.name, message['remote_user_id'], u.user_id, sign_md5)
                camu.append({'user_id': u.user_id, 'link': link})

            for u in online_users:
                mess = {"act" : "update_tpa_online_indicarors", 'user_list': ou }
                dest = 'tpa_channel_%s_%s' % (message['tpa_id'], u.id)
                c.publish(dest, json.dumps(mess)) 
            for u in online_users:
                mess = {"act" : "update_tpa_watch_indicarors", 'cam_list':  camu}
                dest = 'tpa_channel_%s_%s' % (message['tpa_id'], u.id)
                c.publish(dest, json.dumps(mess)) 


        # disconnection from tpa js script
        if message['act'] == 'tpa_disconnect':
            ChatUser.objects.filter(tpa_id=message['tpa_id'], id=message['user_id']).update(is_online=0)



        if message['act'] == 'refresh_video_indicators':
            message = {"act" : "refresh_video_indicator"}
            self.broadcast(self.participants, json.dumps(message))         
      

        if message['act'] == 'i_agree_to_private_chat':
            rooms = self.get_all_active_rooms()
            #for r in rooms:
            #    r.close_me(self.current_user) ### not need becouse at least one common apponent can invite you to private
            room = self.get_or_create_room(int(message['caller']),int(message['user_id']),'private')
            # mark woman as busy for another private invitations
            if room.typeroom=='private' and self.current_user.gender == 'w':
                user = ChatUser.objects.get(pk=self.current_user.id)
                user.now_in_private = True         
                user.save()
            self.room = room
            if int(message['caller'])!=self.current_user.pk:
                caller = int(message['user_id'])    
            else:
                caller = int(message['caller'])
            # put woman to room
            mes = { "act" : "put_me_in_room", "room_id" : room.pk, 'uid' : caller}
            c.publish('%s_%s' % ( self.tpa.id, self.current_user.pk ), json.dumps(mes))
            #put man to room
            mes = { "act" : "put_me_in_room", "room_id" : room.pk, 'uid' : caller}
            c.publish('%s_%s' % ( self.tpa.id, message['user_id'] ), json.dumps(mes))
            mes = { "act" : "pop_up_message", "message" : _('Woman just accepted your invitation.'), 'delay' : 3000}
            c.publish('%s_%s' % ( self.tpa.id, message['user_id'] ), json.dumps(mes))
            mes = { 'act': 'clear_video_slots' }
            c.publish('%s_%s' % ( self.tpa.id, message['user_id'] ), json.dumps(mes)) 
            mes = { 'act': 'add_video_to_slot', 'uid': caller }
            c.publish('%s_%s' % ( self.tpa.id, message['user_id'] ), json.dumps(mes))  
            #c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))

        if message['act'] == 'i_denite_to_private_chat':
            mes = { "act" : "pop_up_message", "message" : _('Sorry, but woman just reject your invitation.'), 'delay' : 3000}
            c.publish('%s_%s' % ( self.tpa.id, message['user_id'] ), json.dumps(mes))       

        elif message['act'] == 'invite_from_chat':
            opponent = ChatUser.objects.get(pk=message['uid'])

            if  opponent.gender == 'm':  # a woman invite a men               
                if message['type'] == 'spy':
                    logger.debug('Invitation to man from chat (spy) to uid:%s from uid:%s' % (message['uid'], message['caller']))
                    room = self.get_or_create_room(message['caller'],message['uid'],'spy')
                    chanel = 'wc_%s_%s' % (message['uid'], self.tpa.id)
                    mes = { 'act': 'show_my_cam', 'chanel': chanel }
                    c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  
                #    #c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes))    
                if message['type'] == 'common':
                    logger.debug('Invitation to man from chat (common) to uid:%s from uid:%s' % (message['uid'], message['caller']))
                    room = self.get_or_create_room(message['caller'],message['uid'],'common')
                    #mes = { 'act': 'i_invite_you_to_common_chat', 'username': self.current_user.name, 'uid': self.current_user.id }
                    #c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes))  
                    mes = { 'act': 'put_me_in_room', 'room_id': room.id, 'uid': message['uid'] }
                    c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  

 
         
                  
                
            if  opponent.gender == 'w': # a man invite a woman
                if opponent.now_in_private == True:
                    mes = { "act" : "apponent_is_busy" }
                    c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))
                else:
                    if message['type'] == 'spy':
                        logger.debug('Invitation to woman from chat (spy) to uid:%s from uid:%s' % (message['uid'], message['caller']))

                        mes = { 'act': 'add_video_to_slot', 'uid': message['uid'] }
                        c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  
                        #c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes)) 

                    if message['type'] == 'common':
                        logger.debug('Invitation to woman from chat (common) to uid:%s from uid:%s' % (message['uid'], message['caller']))
                        room = self.get_or_create_room(message['caller'],message['uid'],'common')
                        mes = { 'act': 'put_me_in_room', 'room_id': room.id, 'uid': message['uid'] }
                        c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  

                        mes = { 'act': 'put_me_in_room', 'room_id': room.id, 'uid': message['uid'] }
                        c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes)) 

                        mes = { 'act': 'add_me_to_online', 'uid': message['uid'] }
                        self.broadcast(self.participants, json.dumps(mes))

                        logger.debug('Adding %s to online.' % (message['uid'] ))                   
                        #c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes)) 
                       
                    if message['type'] == 'private':
                        logger.debug('Invitation to woman (uid:%s) to private chat from uid:%s' % (message['uid'], message['caller']))
                        room = self.get_or_create_room(message['caller'],message['uid'],'private')

                        #mes = { 'act': 'put_me_in_room', 'room_id': room.id, 'uid': message['caller'] }
                        #c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))
                        #logger.debug('Put %s in room %s' % ( self.tpa.id, message['caller'] ))

                        #mes = { 'act': 'add_video_to_slot', 'uid': message['uid'] }
                        #c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  

                        mes = { 'act': 'notify_about_private_invitation', 'room_id': room.id, 'uid': message['caller'], 'avatar': self.current_user.image, 'message': _('This user invite you to the private chat. You have 3 min to accept.'), 'user_name':  self.current_user.name}
                        c.publish('%s_%s' % ( self.tpa.id, message['uid'] ), json.dumps(mes))



                        mes = { 'act': 'waiting_for_accept_private_chat' }
                        c.publish('%s_%s' % ( self.tpa.id, message['caller'] ), json.dumps(mes))  


                        #logger.debug('Put %s in room %s' % ( self.tpa.id, message['uid'] ))

                        mes = { 'act': 'delete_me_from_online', 'uid': message['uid'] }
                        self.broadcast(self.participants, json.dumps(mes))
                        logger.debug('Deleting %s from online.' % (message['uid'] ))

                        

     

        # Money spending...
        elif message['act'] == 'deduct': 
            try:
                self.swith_room(message['room_id'])
            except:
                pass
  
            price = 0
            for t in message['videos']:
                arr = t.split('_')
                woman = ChatUser.objects.get(pk=int(arr[1]))
                t = ChatTransactions()
                t.man = self.current_user
                t.woman = woman
                t.ammount = self.price_spy
                t.tpa = self.tpa
                t.save()
                if(self.current_user.gender=='m'):
                    remoute_deduct(self.current_user,self.tpa, 'watching', woman)
                #import pdb; pdb.set_trace()
                #self.account = self.account - price

            user = ChatUser.objects.get(pk=self.current_user.id)
            if self.account<=0:
                mes = { "act": "empty_account"}
                if self.is_noticed_about_empty_account == False:
                    c.publish(self.identifier, json.dumps(mes))
                    self.is_noticed_about_empty_account = True
                    user.account = 0
                    user.save()
                    #mes = { "act": "update_account", "account":  '0.00'}
                    #c.publish(self.identifier, json.dumps(mes))
            else:
                user.account = user.account - price
                user.save()
                #mes = { "act": "update_account", "account":  str(user.account)}
                #c.publish(self.identifier, json.dumps(mes))
                self.room.duration = self.room.duration + 60
                self.room.save()

        # Sending a message to opponent
        elif message['act'] == 'send_message':
            # Check for money
            if self.current_user.account == 0  and self.current_user.gender == 'm' :
                # Send error message couse of no money
                mes = { "act": "empty_account"}
                c.publish(self.identifier, json.dumps(mes))
                return True

            # Set servers locale to Kiev time to save same date of message for girl and man
            import pytz, datetime
            local = pytz.utc
            naive = datetime.datetime.strptime (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone (pytz.timezone ("Europe/Kiev"))

            # Send current message to both of interlocutors
            for r in message['recipients']:
                print "publishing to %s" % (r,)
                c.publish(r, json.dumps({
                                         "timestamp" : int(time.time()), # Time of message sent in seconds
                                         "time" : utc_dt.strftime ("%H:%M:%S"), # Time that opponents see in the chat
                                         "content" : message['message'], # Message, properly
                                         "gender" : message['gender'], # Gender of user who sent message
                                         "uid" : message['uid'], # ID of user who sent message
                                         "name" : message['name'], # Name of user who sent message
                                         "room_id" : message['room_id'], # Current room id
                                         "act" : "send_message"
                                        }))

            # Change current room if message sent to opponent in another room
            #import pdb; pdb.set_trace()
            self.swith_room(message['room_id'])

            # Save message to database in the backend of Tornado server
            message = save_chat_message.delay(self.current_user, message['message'], self.tpa, self.room)
           
            
            make_room_as_charging(self.room)
    
    # Get is connection successfull or not ( True or False )
    # Create ChatUser2Room object if it needs
    def get_connection_or_create(self, message):
        # Connection from the site
        if message['place'] == 'site' :
            # Get Tpa object
            try:
                tpa = Tpa.objects.get(pk = int(message['tpa']))

            # If it is not exist - FAIL CONNECTION
            except Exception, e:
                logger.debug(e)
                return False
            
            # Get current user information
            try:
                user = ChatUser.objects.get(tpa_id = tpa.id, user_id = int(message['user_id']))
                
            # If user does not exist - get the information from site and add him to Chat system
            except Exception, e:
                signature = md5.new(str(tpa.id) + 'uinfo' + str(message['user_id']) + tpa.secret).hexdigest()
                url = '%s?action=uinfo&uid=%s&sign=%s' % ( tpa.api_link, message['user_id'], signature )
                response = utils.make_request(url, {})
                person = utils.add_or_edit_user(response)
                user = person['user']
        
        # Connection from the chat
        else:
            # Get current user information
            try:
                user = ChatUser.objects.get(pk = int(message['user_id']))

            # If he is not exist - FAIL CONNECTION
            except Exception, e:
                logger.debug(e)
                return False

            # Get Tpa object from ChatUser object
            tpa = user.tpa

        # Set user is online and save the rest information we will need
        try:
            user.is_online = 1
            user.save()
            self.profile = user
            self.is_auth = 'true'
            set_user_online(user, tpa)
        except Exception, e:
            self.is_auth = 'false'
            logger.debug(e)
            return False

        self.current_user = user
        self.tpa = tpa
        self.account = user.account
        self.price_common = tpa.price_common
        self.price_private = tpa.price_private
        self.price_spy = tpa.price_spy
        self.identifier = '%s_%s' % ( tpa.id, user.id )

       

        # Equal self.room and ChatRoom object we get with id = message['room_id'] if we can
        try:
            self.room = ChatRoom.objects.get(pk = int(message['room_id']))
        except Exception, e:
            logger.debug(e)

        return True


    
    # When current user tries to disconnect
    def on_close(self):
        #logger.debug('User close ------- %s ' % self.tpa.id)
        # Close the connection
        #import pdb; pdb.set_trace()
        if self.place == 'tpa':
            time_mark = int(time.time())
            result = set_user_offline.apply_async((self.current_user, self.tpa, time_mark), countdown=15)
            #result.get()
            #set_user_offline.delay(self.current_user, self.tpa)
        else:
            user = ChatUser.objects.get(id=self.current_user.id)
            user.now_in_private = False
            user.is_camera_active = False
            user.is_private_allow = True
            user.is_online = 0
            user.save()
        #ChatUser2Room.objects.filter(user=self.current_user).update(is_camera_active=False)
            message = json.dumps({ "uid" : self.current_user.id, "act" : "i_close_chat_conection" })
            #try:
            #    apponents = self.room.get_participants_except_user(self.current_user)
        #    for a in apponents:
        #        dest = '%s_%s' % (self.tpa.id, a.id)
                #import pdb; pdb.set_trace()
        #        c.publish(dest, message)
            
        #    message = json.dumps({ "uid" : self.current_user.id, "act" : "delete_me_from_online" })
            # Remove client from the clients list and broadcast leave message
        #    self.participants.remove(self)
            self.broadcast(self.participants, message)
        #except:
        #    pass


        logger.debug('User ' + str(self.current_user.id) + ' has left the room') # Debug        


    
    # Generate current users identifier
    def get_connection_sign(self):
        return '%s_%s' % (str(self.tpa.id), str(self.current_user.id))
        
    def get_all_active_rooms(self):
        sql = 'select main_chatroom.* from main_chatroom, main_chatuser2room where main_chatuser2room.room_id=main_chatroom.id and main_chatuser2room.user_id=%s' % self.current_user.id
        return ChatRoom.objects.raw(sql)
        
    def get_or_create_room(self,caller_id,callee_id, typeroom):
        
        caller = ChatUser.objects.get(pk=caller_id)
        #callee = ChatUser.objects.get(pk=callee_id)
        room = create_room_if_not_exists(caller, callee_id,self.tpa,typeroom).roomobj

        return room
        
    def swith_room(self,room_id): 
        try:       
            if self.room.id != int(room_id) :
                try:
                    self.room = ChatRoom.objects.get(pk = int(room_id))
                except Exception, e:
                    logger.debug(e)
        except:
            pass
####################################################################################################

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # 1. Create chat router
    #ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/chatws')
    #ChatRouterws = sockjs.tornado.SockJSRouter(ChatConnection, '/chatws')
    #ChatRouter = sockjs.tornado.So(ChatConnection, '/chatws')

    # 2. Create Tornado application
    app = tornado.web.Application(
            [
             (r"/av/$",AvatarHandler),
             (r"/", IndexHandler),
            ] + ChatRouter.urls +  ChatRouterws.urls
    )

    # 3. Make Tornado app listen on port 8080
    app.listen(2222)

    # 4. Start IOLoop
    tornado.ioloop.IOLoop.instance().start()
