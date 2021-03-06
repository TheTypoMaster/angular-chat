/*"""
videoCtrl.js
``````````````


Manipulate with video blocks.
 


*/

app.controller('VideoCtrl', function ($scope, $rootScope, $window, $log, Video,$interval, WS, Room) {


         $rootScope.active_cams = {}

        /*"""
        .. function:: $scope.$on('rootScope_ready'...


<param name="FlashVars" value="codecOn=true&ww=800&hh=600&fps=20&streamName={{ token }}&url=rtmp://{{ rtmp_domain }}/myapp&micOn=false&type={{ type }}" />

           
        */ 
      $scope.isMyVideoActive = false;

      $scope.showMyVideo = function(){

            if($rootScope.gender=='m') {
               var with_audio = true;          
            } else {
               var with_audio = false; 
            }            

            var par = { flashvars:"codecOn=true&ww=800&hh=600&fps=20&streamName="+local_config.app_name+'_'+$rootScope.currentUserId+"&url=rtmp://chat.mirbu.com/myapp&micOn="+with_audio+"&type=out" };
            swfobject.embedSWF("Media/chat.swf", "myVideo", "100%", "100%", "9.0.0", "expressInstall.swf", par);
            $scope.isMyVideoActive = true;

            Video.showMyCam(function(){
                
            })
            
        }

  
      $scope.hideMyVideo = function(){

            $(document).find('#myVideoContainer').html('<div id="myVideo"> There are no cameras are available or installed </div>');
            //swfobject.removeSWF("myVideo");
            $scope.isMyVideoActive = false;

            Video.hideMyCam(function(){
                
            })

        }


      $scope.turnMicOn = function(){
         document["myVideo"].JsTurnMicOn();
         log(document["myVideo"]);
         $scope.is_mic_on = true;
         Video.turnMicOn(function(result){
            
         })
      }


      $scope.turnMicOff = function(){

        document["myVideo"].JsTurnMicOff();
        $scope.is_mic_on = false;
         Video.turnMicOff(function(result){
            
         })
      }





      $scope.showOpponentVideo = function(){

                
                var par = { flashvars:"codecOn=true&ww=800&hh=600&fps=20&streamName="+local_config.app_name+'_'+$rootScope.current_opponent_id+"&url=rtmp://chat.mirbu.com/myapp&micOn=true&type=in" }; 
                

                if($rootScope.gender=='m') { // if man check balance and turn charging every min

                    Room.getBalance().then( function(result){

                        if(result.data.status==1){

                            $rootScope.emptyAccountAlert();
                            
                        } else {

                             swfobject.embedSWF("Media/chat.swf", "opponentVideo", "100%", "100%", "9.0.0", "expressInstall.swf", par);
                             $rootScope.isOpponentCamEnabled = true;
                             Video.showOpponentCam($rootScope.current_opponent_id,function(result){
                                // Initiate periodic calling to charge money
                                /*
                                $scope.invite_promise = $interval(function(){

                                    WS.send({ 'action': 'video_charge', 
                                              'user_id': $rootScope.currentUserId, 
                                              'app_name': local_config.app_name, 
                                              'opponent_id': result.user_id, 
                                              'room_id': $rootScope.room_id 
                                            });

                                }, 10000);
                                */
                             })

                        }
                    })                

                } else { // if woman just turn cam on

                        $rootScope.isOpponentCamEnabled = true;
                        swfobject.embedSWF("Media/chat.swf", "opponentVideo", "100%", "100%", "9.0.0", "expressInstall.swf", par);
                }
        
               
            
                        
            }

           

            
        


      $scope.hideOpponentVideo = function(){
       
            swfobject.removeSWF("opponentVideo");
            $(document).find('#oponent_video_container').append('<div id="opponentVideo"> </div>');
            $rootScope.isOpponentCamEnabled = false;
         
             Video.hideOpponentCam($rootScope.current_opponent_id, function(){
                if (angular.isDefined($scope.invite_promise)) {
                    $interval.cancel($scope.invite_promise);
                    $scope.invite_promise = undefined;
                }                
            })          

        }

    $rootScope.$on('close_video',function(event,data){

        $scope.hideOpponentVideo();
        $rootScope.emptyAccountAlert();
    })


    $rootScope.$on('update_cam_indicators',function(event,data){

        if(data.cam_status=='on') {
          $rootScope.active_cams['user_'+data.owner] = true;
        }   else {
          $rootScope.active_cams['user_'+data.owner] = false;
        }
        
        log($rootScope.active_cams);
        if (!event.defaultPrevented && typeof $rootScope.room_participants !== 'undefined') {
            event.defaultPrevented = true;
            for (var i = 0; i < $rootScope.room_participants.length; i++) {
                var val = $rootScope.room_participants[i];
                var arr = val.split('_');
                log(arr);
                if(arr[1]==data.owner && data.owner!= $rootScope.currentUserId){
                    log(data);
                    if(data.cam_status=='on') { 
                        $rootScope.isOpponentVideoActive = true;
                    } else {
                        swfobject.removeSWF("opponentVideo");
                        $(document).find('#oponent_video_container').append('<div id="opponentVideo"> </div>');
                        $rootScope.isOpponentVideoActive = false;
                    }
                    
                    $rootScope.isOpponentCamEnabled = false;
                    $rootScope.opponent_id = data.owner;
                    
                }
            }
        //console.log('camera'+data.owner);

        //console.log($rootScope.room_participants);
            
        }

       
    });
     

     

    })




