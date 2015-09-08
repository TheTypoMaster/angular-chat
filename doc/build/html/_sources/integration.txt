Integration
===========

Add follows javascripts into your header section.

.. code-block:: html

     <script src="/chatapp/app.js"></script>
     <script src="/chatapp/controllers/controllers.js"></script>
     <script src="/chatapp/controllers/roomCtrl.js"></script>
     <script src="/chatapp/routers.js"></script>
     <script src="/chatapp/services/Auth.js"></script>
     <script src="/chatapp/services/Online.js"></script>
     <script src="/chatapp/services/Contact.js"></script>
     <script src="/chatapp/services/Room.js"></script>
     <script src="/chatapp/directives/chat-invitation.js"></script>
     <script src="/chatapp/directives/chat-translator.js"></script>
     <script src="/chatapp/services/websocket.js"></script>
     <script src="/chatapp/utils.js"></script>
     <script src="/chatapp/config.js"></script>
     <script src="/chatapp/local_config.js"></script>


Add follows javascripts into the bottom of your page.

.. code-block:: html

     <script src="/chatapp/utils.js"></script>
     <script src="/chatapp/tpapp.js"></script>
     <script src="/chatapp/services/websocket.js"></script>
     <script src="/chatapp/services/Online.js"></script>
     <script src="/chatapp/config.js"></script>
     <script src="/chatapp/local_config.js"></script>


Online indicator.
-----------------

.. code-block:: html  

    <x-online-indicator uid="online.user_<?php echo $user->id ?>"></x-online-indicator>

This angular directive will use this thml template which will replace x-online-indicator tag.

.. code-block:: html 

    <p class="online online/offline">Online now</p>

Or you can use ng-show directive to show and hide online indicator depending on  online.user_id variable in the angular's scope.

.. code-block:: html

    <a class="like int_pop" href="#invite_pop" ng-show="online.user_<?php echo $user->id ?>"></a>

Chat actions.
-------------

All the chat icons have to be inside html block with ng-controller="ActionCtrl" attribute.
-----------------------------------------------------------------------------------------

For example: 

.. code-block:: html 

            <div class="servise" ng-controller="ActionCtrl">
            <ul data-id="<?php echo $man->id; ?>">
               
                <li ng-show="activecam.user_<?php echo $man->login ?>"><a ng-click="invite(<?php echo $man->login ?>)" class="web_chat "></a></li>
                <li ng-show="online.user_<?php echo $man->login ?>" ><a ng-click="invite(<?php echo $man->login ?>)" class="chat "></a></li>

            </ul>
        </div>

Active cam indicator.
---------------------

.. code-block:: html

    <li ng-show="activecam.user_<?php echo $girl->id ?>"></li>


Inviting link.
--------------

This link will send user to the chat page and put him in the room with opponent which id passed to invite() js function.

.. code-block:: html

    <a ng-click="invite(<?php echo $girl->id ?>)" class="web_chat ">Chat with me</a>








INCOME API
==========

1. Request to get information about user.
=========================================

**URI** http:/[server]/chat-request/profile?user_id=150042

RESPONSE
--------

.. code-block:: json

    { 'status': 0, 
      'user_profile': {
                        'user_id': 150042,
                        'name': 'Oleg',
                        'birthday': '1976-02-03',
                        'country': 'USA', 
                        'city': 'New York',
                        'culture': 'en', 
                        'gender': 'm', 
                        'image': 'http://site.com/oleg.jpg', 
                        'profile_url': 'http://site.com/profile?id=34', 
                        'tpa': 'site_com'
                      }
    }

Where

**tpa** - unique name of the site which was defined after site registration in chat's system.

In case of error.

.. code-block:: json

    { status:1, message: 'User not found'}


2. Request to get know is user authorized or not.
=================================================

**URI** http:/[server]/chat-request/isLogin

RESPONSE:
---------

if logined

.. code-block:: json

    {"id":"150046","gender":"m","balance":"1000.00","success":true}

if not 

.. code-block:: json

    {"id":"0" ,"success":false}

3 Request to get user's balance.
================================

**URI** http:/[server]/chat-request/getBalance?user_id=150040

RESPONSE:
---------

.. code-block:: json

    {'status': 0, 'user_id': 150040, 'balance': 35}

Where **status** define the necessity of notify user about low balance.

If **status** is 1 user will see pop up window with link directed to the billing page.
 


4. Request of charging money from user's account for text chating or video.
===========================================================================

REQUEST
-------

**url**: http://[server]/chat-request/charge

.. code-block:: json

            [
                
                    { 
                      'action': 'text_chat', 
                      'app_name': 'bridescom', 
                      'user_id': 150040, 
                      'opponent_id': 150042, 
                      'room_id': 23, 
                      'price': 2
                    },

                    { 
                      'action': 'video', 
                      'app_name': 'bridescom', 
                      'user_id': 150040, 
                      'opponent_id': 150042, 
                      'room_id': 23, 
                      'price': 3
                    }
                    
            ]
             

Json data represents group of payments where 

**user_id** - man

**opponent_id** - woman
 
**room_id** - identifier of the chat room. This parameter make it possible to collect the same payments in the one record of the database.


RESPONSE
--------

.. code-block:: json

    [
        {'user_id': 150040, 'balance': '23.78'},
        {'user_id': 150041, 'balance': '20.03'}
    ]


5. Request to add/remove user to/from the contact list.
=======================================================

**URI** http://[server]/chat-request/contact


REQUEST
-------

.. code-block:: json

    {'user_id': 150040, 'opponent_id': 150032, 'action': 'add/delete'}


RESPONSE
--------

.. code-block:: json

    { status:0, message: 'ok'}



.. code-block:: json

    { status:1, message: 'User not found'}


.. code-block:: json

    { status:1, message: 'Contact is aleady exists'}



6. Request to add/remove/get user's favorites.
==============================================

**URI** http://[server]/chat-request/favorites
 

REQUEST
-------

.. code-block:: json

    { 'user_id': 150040, 'opponent_id': 150032, action: 'add' }
    { 'user_id': 150040, 'opponent_id': 150032, action: 'remove' }
    { 'user_id': 150040, action: 'get' }


VERSIONS OF THE RESPONSES
-------------------------

.. code-block:: json

    { status:0, message: 'ok'}
    { status:1, message: 'This user is already exists in your favorite list'}
    { status:1, message: 'User not found'}
    { status:0, favorite_list: [150032, 150064 ... ]}


HOW TO GET INFORMATION FROM REQUEST BODY IN PHP

.. code-block:: php

    $result = file_get_contents('php://input');
    $result = json_decode($result);
    




7. Request to block/unblock user.
=================================

**URI** http://[server]/chat-request/block


REQUEST
-------

.. code-block:: json

    { 'user_id': 150040, 'opponent_id': 150032, 'action': 'block/unblock' }


RESPONSE
--------

.. code-block:: json

    { status:0, message: 'ok'}


.. code-block:: json

    { status:1, message: 'User not found'}


8. Request to chek if user blocked or not.
==========================================

**URI** http://[server]/chat-request/is_blocked?user_id=150014&blocked_id=150040

Where: 

**user_id** - user who is checking, and who want to talk with

**blocked_id** - user who could block user who is checking


RESPONSE
--------

.. code-block:: json

    { status:0, is_blocked: 'yes/no'}


.. code-block:: json

    { status:1, message: 'User not found'}


9. Request to send message in message box.
==========================================

**URI** http://[server]/chat-request/send_message

REQUEST
-------

.. code-block:: json

    { 'from_id': 150040, 'to_id': 150032, 'message': 'Hello my friend!!!' }

Where: 

**from_id** - user who send the message

**to_id** - user who receive the message




RESPONSE
--------

.. code-block:: json

    { status:0, message: 'ok'}


.. code-block:: json

    { status:1, message: 'Not enought money'}






OUTCOME API
===========


1. Request to add user to the contact list.
===========================================

REQUEST
-------


**URI** http://[server]/api/[app_name]/[owner_id]/[contact_id]/add_contact

**[app_name]** - application identifire that was given after registration in the chat system.

RESPONSE
--------

.. code-block:: json

        Responce 1: { 'status': 0, 'message': 'Contact has been added' }

        Responce 2: { 'status': 1, 'message': 'Contact is already exists' }  



2. Request to remove user from the contact list.
================================================

REQUEST
-------

**URI** [server]/api/[app_name]/[owner_id]/[contact_id]/del_contact
        
**Example:** http://chat.localhost/api/tpa1com/14/15/del_contact

.. code-block:: json

    Responce 1: { 'status': 0, 'message': 'Contact has been deleted' }

    Responce 2: { 'status': 1, 'message': 'Contact does not exist.' }


3. Request to update user's information or create new one if he does not exist.
===============================================================================

**URI** http://[server]/api/[app_name]/[user_id]/update_user

Example:
-------- 

**http://brides.mirbu.com/api/tpa1com/510027/update_user**

Where:
------

[app_name] - site name 'tpa1com'

[user_id] - user indentifier




