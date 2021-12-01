from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<str:article_id>/',views.article, name='article'),
    path('tat/', views.tat, name='tat'),
    path('about/', views.about, name='about'),
    path('how/', views.how, name='how'),
    path('faq/', views.faq, name='faq'),
    path('therapist/', views.therapist, name='therapist'),
    # auth
    path('login/', views.login, name='login'),
    path('logout/',views.logout, name="logout"),
    path('signup_user/',views.signup_user, name='signup_user'),
    path('signup_psych/',views.signup_psych, name='signup_psych'),
    # psych
    path('create_meet/',views.create_meet, name='create_meet'),
    path('meets_upcoming/',views.meets_upcoming, name='meets_upcoming'),
    path('requests_page/',views.requests_page, name='requests_page'),
    # requests
    path('create_request/',views.create_request, name='create_request'),
    path('make_request/',views.make_request, name='make_request'),
    path('profile/<str:email>//',views.profile, name='profile'),
]