(function () {
  'use strict';

  angular
    .module('AngularChatApp')
    .factory('WS', function($websocket, $rootScope){

      var dataStream = $websocket("ws://"+apiconf.config.ws_server+"/ws");


      dataStream.onMessage(function(message) {
        message = JSON.parse(message.data)
        console.log(message);

        if(message.action=='connected'){
            
            $rootScope.$broadcast('connected');
                   
        }



        if(message.action=='update_contact'){
            
            $rootScope.$broadcast('update_contact');
                   
        }

        if(message.action=='put_me_in_room'){
            
            $rootScope.$broadcast('put_me_in_room', {'room_id': message.room_id, 'owner_id': message.owner_id, 'contact_id': message.contact_id});
                   
        }

        if(message.action=='show_inv_win'){
            
            $rootScope.$broadcast('show_inv_win',{'message':message}); 
            alert("fgdfgdfg")                   
        }


        if(message.action=='update_users_online'){
            
            $rootScope.$broadcast('update_users_online');
                   
        }

        if(message.action=='show_message'){

            $rootScope.$broadcast('show_message', {'message':  message.message});
                   
        }
        
        /**
        * Request after sending invitation or accepting invitation
        *
        */
        if(message.action=='put_user_to_room'){

            $rootScope.$broadcast('put_user_to_room', {'message':  message.message});
                   
        }


      });

      dataStream.onOpen(function(message) {
        
      });


      var methods = {

        send: function(mess) {
          dataStream.send(JSON.stringify(mess));
        }

      };

      return methods;   

    });


})();
