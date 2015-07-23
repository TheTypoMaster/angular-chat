from django.shortcuts import render
import json
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as login_user
from chat.models import Tpa, ChatUser, ChatContacts
from djapp.settings import DATABASES
import PySQLPool
import requests
from utils.util import read_conf

def home(request):
    t = loader.get_template('base.html')
    c = RequestContext(request,{})
    return HttpResponse(t.render(c))

@csrf_exempt
def get_online(request,app_name):
    #import pdb; pdb.set_trace()
    userlst_profile = []
    tpa = Tpa.objects.get(name=app_name)
    for u in ChatUser.objects.filter(tpa=tpa,is_online=1):
        userlst_profile.append(serialize_user(u))
    out = { 'status': 0, 'message': 'ok', 'user_list': userlst_profile }
    return HttpResponse(json.dumps(out), content_type='application/json')  

@csrf_exempt
def get_contact_list(request,app_name):
    import pdb; pdb.set_trace()
    contactlst = []
    tpa = Tpa.objects.get(name=app_name)
    for c in ChatContacts.objects.filter(tpa=tpa):
        contactlst.append({'owner':c.owner.name,'contact':c.contact.name})
    out = { 'status': 0, 'message': 'ok', 'contact_list': contactlst }
    return HttpResponse(json.dumps(out), content_type='application/json')  
        

def has_opponent(request,user_id):
    out = {
        'status': 1,
        'contact_id': 5
    }
    return HttpResponse(json.dumps(out), content_type='application/json')  



def is_auth(request,app_name):
    if(request.user.is_authenticated()):
        out = {
            'status': 0,
            'user_id': request.user.id,
            'username': request.user.username
        }
    else:
        out = {
            'status': 1,
            'message': 'user is not authorized'
        }
    return HttpResponse(json.dumps(out), content_type='application/json')  

@csrf_exempt
def login(request):
    #import pdb; pdb.set_trace()
    #data = json.loads(request.body)
    username = request.POST['username']
    password = request.POST['password']
    
    
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login_user(request,user)
            out = { 'status': 0, 'message': 'ok', 'username': user.username, 'user_id': user.id }
        else:
            out = { 'status': 1, 'message': 'Password does not match!' }
    except:
        out = { 'status': 1, 'message': 'User does not found!' }
        
    context = { }
   
    return HttpResponse(json.dumps(out), content_type='application/json')  

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    out = {
        'status': 0,
        'message': 'ok',
    }
    return HttpResponse(json.dumps(out), content_type='application/json')   


def get_profile_from_tpa(request,user_id):
    connection = PySQLPool.getNewConnection(username=DATABASES['default']['USER'],
                 password=DATABASES['default']['PASSWORD'], host=DATABASES['default']['HOST'],
                 db=DATABASES['default']['NAME'])
    query = PySQLPool.getNewQuery(connection)
    query.Query('select * from users_info where user_id = %d' % int(user_id))
    for row in query.record:
        print row['name']
        out = {
        'status': 0,
        'message': row['name'],
        }
    try:
        return HttpResponse(json.dumps(out), content_type='application/json') 
    except:
        return HttpResponse(json.dumps({
        'status': 1,
        'message': 'no user found',
        }), content_type='application/json')

def get_profile(request,user_id):
    try:
        u_name = ChatUser.objects.get(user_id=user_id)
        out = {
            'status': 0,
            'user_profile': serialize_user(u_name)
        }
        return HttpResponse(json.dumps(out), content_type='application/json')
    except:
        apiconf = read_conf()
        print apiconf
        url = 'http://'+apiconf['api']['get_profile_from_tpa']['url']
        url = url.replace('[server]',apiconf['config']['signal_server'])
        url = url.replace('[user_id]',user_id)
        print 'REQUEST TO %s' % url
        responce = requests.get(url)
        outdata = json.loads(responce.content)
        print outdata  
       
        out = {
            'status': 0,
            'message': 'ok',
            'outdata': outdata
        }
        return HttpResponse(json.dumps(out), content_type='application/json')

def serialize_user(user):
    return ({'user_id':user.id,'gender':user.gender,'name':user.name,'age':user.age,
                    'country':user.country,'city':user.city,'image':user.image,
                    'profile_url':user.profile_url,'culture':user.culture,
                    'is_camera_active':user.is_camera_active, 
                    'is_invisible': user.is_invisible, 
                    'is_invitation_enabled': user.is_invitation_enabled})

