# -*- coding: utf-8 -*-
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import json
from processor import handle
import logging
import brukva
c = brukva.Client()
c.connect()
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
import requests
import time
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../djapp'))
from utils.api_router import get_url_by_name
from utils.db import MyDB
bd = MyDB()
import sockjs.tornado
 
class WSHandler(tornado.websocket.WebSocketHandler):
    '''
    Websocket server that uses the Tornado websocket handler.
    Please run `pip install tornado` with python of version 2.7.9 or greater to install tornado.
    ''' 
    participants = set() # List of users online

    def broadcast(self, msg):
        for p in self.participants:
            try:
                p.write_message(json.dumps(msg))
            except:
                pass

    def __init__(self,*args):
        '''Initialization'''
        super(WSHandler, self).__init__(*args)  
        self.client = brukva.Client()
        self.client.connect()
        self.current_user_id = None
        self.tpa_name = None
        self.processor = None

    def open(self):
        print 'new connection'
        self.participants.add(self)

    def subscribe(self, room):
        '''Subscribing user to the channel in the REDIS server'''
        self.client.subscribe(room) # Redis subscribe
        logger.debug('subscribing to room %s' % (room, )) # Debug
        self.client.listen(self.redis_message)

    def pass_message(self, message):
        self.write_message(json.dumps(message)) 

      
    def on_message(self, message):
        'Accepting message from javasctipt client'
        #print 'message received:  %s' % message
        message = json.loads(message) 

        if message['action'] == 'connect':
            try:
                url = get_url_by_name('set_connected',{'user_id':message["user_id"], 'app_name': message["tpa"]})
                requests.get(url)
                chanel = '%s_%s' % (message["tpa"], message["user_id"])
                self.subscribe(chanel)
                self.current_user_id = message["user_id"]             
                self.tpa_name = message["tpa"]

                self.write_message(json.dumps({'action': 'connected', 'status': 0, 'user_id':  self.current_user_id, 'message': 'you have been connected to %s' % chanel })) 
                #self.set_user_online()
                #mes = {'action': 'update_users_online'}
                #self.broadcast(mes)     
                #mes = {'action': 'set_me_online', 'uid': self.current_user_id}
                #self.broadcast(mes)
                #print 'set me online!!!!!!!!!!!!'  
            except Exception, e:
                print e
                self.write_message(json.dumps({'status': 1, 'message': str(e)})) 
          
        handle(message,self)
        
        

 
    def on_close(self):
        ''' Method whith fires when connection is closed. '''
        print 'connection closed'
        url = get_url_by_name('set_disconnected',{'user_id':self.current_user_id, 'app_name': self.tpa_name})
        requests.get(url)
        #self.set_user_offline()
        #mes = {'action': 'update_users_online'}
        #self.broadcast(mes) 
        #mes = {'action': 'set_me_offline', 'uid': self.current_user_id}
        #self.broadcast(mes) 
        self.participants.remove(self)


    #def set_user_online(self):
    #    bd.update('update chat_chatuser set is_online=1 where user_id=%s and tpa_id=%s' % (self.current_user_id, self.tpa_id))
    #    bd.update('update users set online=1 where login=%s' % self.current_user_id)

    def set_user_offline(self):
        bd.update('update chat_chatuser set is_online=0 where user_id=%s and tpa_id=%s' % (self.current_user_id, self.tpa_id))
        

    def redis_message(self, result):
        ''' recieving  message from redis server, 
            convertin it in json format 
            and sending it to the current chanel
        '''
        
        message = json.loads(result.body)
        #print message
        #self.write_message(json.dumps({'status': 1}))
        try:
            self.write_message(json.dumps(message))
        except:
            print "Can not send %s to %s_%s" % (message,self.tpa_name, self.current_user_id)

 
    def check_origin(self, origin):
        return True
 
application = tornado.web.Application([
    (r'/ws', WSHandler),
])
 


def send_charge_request():
       
    sql = '''select chat_chatroom.id, 
                    chat_chatroom.activity, 
                    chat_chatroom.is_charging_text, 
                    chat_chatroom.is_charging_video, 
                    chat_tpa.price_text_chat, 
                    chat_tpa.price_video, 
                    chat_tpa.charge_url, 
                    chat_tpa.name as app_name, 
                    chat_tpa.timeout_chating
             from chat_chatroom, chat_tpa  
             where 
             chat_chatroom.tpa_id = chat_tpa.id and
             (is_charging_text="%s" or is_charging_video="%s")''' % (1,1)
    rooms = bd.select(sql)
    data = []
    url = False
    for room in rooms.record: 
        url = room['charge_url']
        # select users from room
        sql = ''' select chat_chatuser.user_id, chat_chatuser.gender 
                  from chat_chatuser, chat_chatuser2room
                  where chat_chatuser2room.user_id = chat_chatuser.id 
                        and chat_chatuser2room.room_id = %s 
              ''' % room['id']

        users = bd.select(sql)
        for u in users.record:
            print 'room %s user %s' % (room['id'],u['gender'])
            if u['gender'] == 'm':
                man = u['user_id']
            else:
                woman = u['user_id']

        if(room['is_charging_text']==1):
            now = int(time.time())
            timeout = room['activity']+room['timeout_chating']
            #print 'checking %s %s' % (now,timeout)
            if(now>timeout):
                sql_update = ''' update chat_chatroom set is_charging_text=0 where id = %s  ''' % room['id']
                bd.update(sql_update)
                #print 'TIMOUT   00000000'
            else:
                data.append({'action': 'text_chat', 'app_name': room['app_name'],  'user_id': man, 'opponent_id': woman, 'room_id': room['id'], 'price': str(room['price_text_chat']) })
                #print data
                

        if(room['is_charging_video']==1):     
             data.append({'action': 'video', 'app_name': room['app_name'],  'user_id': man, 'opponent_id': woman, 'room_id': room['id'], 'price': str(room['price_video']) })   
    if url:  
        print "Charge request to %s " % url
        #print "DATA %s" % data
        print requests.post(room['charge_url'],json=data).content  



'''
[
    
        {
          'action': 'text_chat',
          'user_id': 150040,
          'opponent_id': 150042,
          'room_id': 23
        },

        {
          'action': 'text_chat',
          'user_id': 150040,
          'opponent_id': 150043,
          'room_id': 24
        }

]'''

        
        
 


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8889)
    myIP = socket.gethostbyname(socket.gethostname())
    print '*** Websocket Server Started at %s***' % myIP
    tornado.ioloop.PeriodicCallback(send_charge_request, 10000).start()
    tornado.ioloop.IOLoop.instance().start()
    
