from django.shortcuts import render, redirect
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, auth
from pathlib import Path
from pickle import load, dump
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from uuid import uuid4
from typing import Dict, List
from datetime import datetime, timedelta 
from dateutil.parser import parse

config = {
    'apiKey': "AIzaSyCd1euA5iB_oUwD_8nY9hdD0iXF2-RB8RI",
    'authDomain': "fika-1.firebaseapp.com",
    'databaseURL': "https://fika-1.firebaseio.com",
    'projectId': "fika-1",
    'storageBucket': "fika-1.appspot.com",
    'messagingSenderId': "813679959555",
    'appId': "1:813679959555:web:0933007e2370baf660b836",
    'measurementId': "G-1VJSPC2QPD"
  }
cred = credentials.Certificate('main/fika-1-firebase-adminsdk-zofc6-68469eb7e0.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
pyrebase_app = pyrebase.initialize_app(config)
pyrebase_auth = pyrebase_app.auth()

class EventPlanner:
    def __init__(self, guests: Dict[str, str], schedule: Dict[str, str], topic):
        guests = [{"email": email} for email in guests.values()]
        service = self._authorize()
        self.event_states = self._plan_event(guests, schedule, service, topic)

    @staticmethod
    def _authorize():
        scopes = ["https://www.googleapis.com/auth/calendar"]
        credentials = None
        token_file = Path("./main/token.pickle")
        if token_file.exists():
            with open(token_file, "rb") as token:
                credentials = load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('main/credentials.json', scopes)
                credentials = flow.run_local_server(port=0)
            with open(token_file, "wb") as token:
                dump(credentials, token)
        calendar_service = build("calendar", "v3", credentials=credentials)
        return calendar_service

    @staticmethod
    def _plan_event(attendees: List[Dict[str, str]], event_time, service: build, topic):
        event = {"summary": topic,
                 "start": {"dateTime": event_time["start"], 'timeZone': 'Asia/Kolkata'},
                 "end": {"dateTime": event_time["end"], 'timeZone': 'Asia/Kolkata'},
                 "attendees": attendees,
                 "conferenceData": {"createRequest": {"requestId": f"{uuid4().hex}", "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
                 "reminders": {"useDefault": True}
                 }
        event = service.events().insert(calendarId="primary", sendNotifications=True, body=event, conferenceDataVersion=1).execute()
        return event

def home(request):
    docs = db.collection('Articles').stream()
    articles = {}
    for doc in docs:
        articles[doc.id] = doc.to_dict()
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/home.html", {"data":data, "articles":articles})
    else:
        return render(request, "main/home.html", {"articles":articles})

def article(request, article_id):
    article = db.collection('Articles').document(article_id).get().to_dict()
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/article.html", {"data":data, "article":article})
    else:
        return render(request, "main/article.html", {"article":article})

def profile(request, email):
    if 'uid' in request.session.keys():
        user = auth.get_user_by_email(email)
        user_id = str(user.uid)
        info = db.collection('users').document(user_id).get().to_dict()
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/profile.html", {"data":data, "info":info, "user_id":user_id})
    else:
        return redirect('home')

def meets_upcoming(request):
    uid = request.session['uid']
    data = db.collection('users').document(uid).get().to_dict()
    try:
        if 'isPsych' in data.keys():
            docs = db.collection('meets').where('psychId', '==', uid).stream()
        else:
            docs = db.collection('meets').where('userId', '==', uid).stream()
        meets_upcoming = {}
        for doc in docs:
            ts = doc.id
            doc = doc.to_dict()
            if str(doc['dateTime']) > str(datetime.now()):
                meets_upcoming[ts] = doc
    except:
        meets_upcoming = False
    return render(request, "main/meets_upcoming.html", {"data":data, "meets_upcoming":meets_upcoming})

def requests_page(request):
    uid = request.session['uid']
    data = db.collection('users').document(uid).get().to_dict()
    try:
        if 'isPsych' in data.keys():
            docs = db.collection('requests').where('psychId', '==', uid).stream()
        else:
            docs = db.collection('requests').where('userId', '==', uid).stream()
        meet_requests = {}
        for doc in docs:
            ts = doc.id
            doc = doc.to_dict()
            if str(doc['dateTime']) > str(datetime.now()):
                meet_requests[ts] = doc
            else:
                db.collection('requests').document(ts).delete()
    except:
        meet_requests = False
    return render(request, "main/requests_page.html", {"data":data, "meet_requests":meet_requests})

def create_request(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        if request.method == 'POST':
            psych_name = request.POST.get('psych_name')
            psych_email = request.POST.get('psych_email')
            psych_id = request.POST.get('psych_id')
            info = {"psych_email":psych_email,"psych_id":psych_id, "psych_name":psych_name}
            return render(request, "main/make_request.html", {"data":data,"info":info})
        else:
            return redirect('therapist')
    else:
        return redirect('therapist')

def make_request(request):
    if 'uid' in request.session.keys():
        if request.method == 'POST':
            psych_name = request.POST.get('psych_name')
            psych_email = request.POST.get('psych_email')
            psych_id = request.POST.get('psych_id')
            date_time = request.POST.get('date_time')
            topic = request.POST.get('topic')
            user_name = request.POST.get('user_name')
            user_email = request.POST.get('user_email')
            duration = request.POST.get('duration')
            user_id = request.session['uid']
            date_time = parse(date_time)
            timestamp = str(datetime.now())
            data = {"userEmail":user_email, "userId":user_id, "userName":user_name, "psychName":psych_name, "psychEmail":psych_email, "psychId":psych_id, "dateTime":date_time, "topic":topic, "duration":int(duration)}
            db.collection('requests').document(timestamp).set(data)
            message = 'Request sent successfully.'
            user = auth.get_user_by_email(psych_email)
            user_id = str(user.uid)
            info = db.collection('users').document(user_id).get().to_dict()
            uid = request.session['uid']
            data = db.collection('users').document(uid).get().to_dict()
            return render(request, "main/profile.html", {"data":data, "info":info, "user_id":user_id, "message":message})
    return redirect('therapist')

def create_meet(request):
    if 'uid' in request.session.keys():
        if request.method == 'POST':
            date_time = request.POST.get('date_time')
            topic = request.POST.get('topic')
            psych_id = request.session['uid']
            psych_name = request.POST.get('psych_name')
            psych_email = request.POST.get('psych_email')
            user_email = request.POST.get('user_email')
            user_name = request.POST.get('user_name')
            user_id = request.POST.get('user_id')
            duration = request.POST.get('duration')
            ts = request.POST.get('ts')
            s = parse(date_time)
            start = str(s)
            start = start[0:10]+'T'+start[11:]
            end = str(s+timedelta(minutes=int(duration)))
            end = end[0:10]+'T'+end[11:]
            meet = EventPlanner({"user_email": user_email}, {"start": start, "end": end}, topic)
            meet_link = meet.event_states['hangoutLink']
            meet_code = meet_link[24:]
            data = {"userEmail":user_email, "psychName":psych_name, "psychEmail":psych_email,"psychId":psych_id, "userId":user_id, "userName":user_name, "dateTime":s, "topic":topic, "duration":duration, "code":meet_code}
            db.collection('meets').document(ts).set(data)
            db.collection('requests').document(ts).delete()
        return redirect('requests_page')
    else:
        return redirect('login')

def login(request):
    if 'uid' in request.session.keys():
        return redirect('home')
    if request.method == 'GET':
        return render(request, "main/login.html")
    else:
        email = request.POST.get('email')
        password = request.POST.get("password")
        try:
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        except:
            message = "Enter correct email and password"
            return render(request, "main/login.html", {"message":message})
        uid = user['localId']
        request.session['uid'] = str(uid)
        return redirect('home')

def logout(request):
    try:
        del request.session['uid']
    except KeyError:
        pass
    return redirect('home')

def signup_user(request):
    if 'uid' in request.session.keys():
        return redirect('home')
    if request.method == 'GET':
        return render(request, "main/signup_user.html")
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        city = request.POST.get('city')
        password = request.POST.get('password')
        image = request.POST.get('url')
        try:
            user = auth.create_user(email=email, password=password)
            uid = user.uid
        except:
            message = "Email must be unique. Password must contain atleast 6 characters."
            return render(request, "main/signup_user.html", {"message":message})
        data = {"userName":username, "email":email, "mobile":mobile, "age":age, "gender":gender, "city":city, "image":image}
        db.collection('users').document(uid).set(data)
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        request.session['uid'] = str(uid)
        return redirect('home')

def signup_psych(request):
    if 'uid' in request.session.keys():
        return redirect('home')
    if request.method == 'GET':
        return render(request, "main/signup_psych.html")
    else:
        is_psych = request.POST.get('is_psych')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')
        spec = request.POST.get('spec')
        city = request.POST.get('city')
        image = request.POST.get('url')
        calendar = request.POST.get('calendar')
        calendar = str(calendar)
        try:
            user = auth.create_user(email=email, password=password)
            uid = user.uid
        except:
            message = "Email must be unique. Password must contain atleast 6 characters."
            return render(request, "main/signup_psych.html", {"message":message})
        data = {"userName":username, "email":email, "mobile":mobile, "speciality":spec, "isPsych":int(is_psych), "city":city, "image":image, "calendar":calendar}
        db.collection('users').document(uid).set(data)
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        request.session['uid'] = str(uid)
        return redirect('home')

def about(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/about.html", {"data":data})
    else:
        return render(request, 'main/about.html')

def how(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/how.html", {"data":data})
    else:
        return render(request, 'main/how.html')

def tat(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/tat.html", {"data":data})
    else:
        return render(request, 'main/tat.html')

def faq(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        return render(request, "main/faq.html", {"data":data})
    else:
        return render(request, 'main/faq.html')

def therapist(request):
    if 'uid' in request.session.keys():
        uid = request.session['uid']
        data = db.collection('users').document(uid).get().to_dict()
        docs = db.collection('users').where('isPsych', '==', 1).stream()
        therapists = {}
        for doc in docs:
            therapists[doc.id] = doc.to_dict()
        return render(request, "main/therapist.html", {"data":data, "therapists":therapists})
    else:
        return redirect('home')
