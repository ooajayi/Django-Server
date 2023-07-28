"""approvd application URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import re
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve
from . import views

app_name = 'core'

urlpatterns = [
     re_path(r'^$', views.IndexView.as_view(), name='homepage'),
     path('home/', views.LandingPageView.as_view(), name='home'),
     path('contact/', views.handle_contact_form, name='contact'),
     path('setup_profile/', views.setup_profile, name='setup_profile'),
     path('profile/', views.MyProfileView.as_view(), name='my_profile'),
     path('my-studio/', views.MyStudioView.as_view(), name='my_studio'),
     path('listings/', views.ListingsView.as_view(), name='listings'),
     path('listings/<int:pk>/', views.ListingDetailsView.as_view(), name='listing_detail'),
     path('topics/', views.ForumTopicsView.as_view(), name='topics'),
     path('topics/<int:pk>/', views.ForumTopicDetailsView.as_view(), name='topic_detail'),

     path('profiles/', views.ProfilesListView.as_view(), name='profiles'),
     path('creators/', views.CreatorsListView.as_view(), name='creators'),
     path('studios/', views.StudiosListView.as_view(), name='studios'),
     path('events/', views.events_calendar, name='events_calendar'),
     path('studio/<str:username>/<int:pk>/',
          login_required(views.studio_details), name='studio_details'),
     path('profile/<str:username>/',
          login_required(views.profile_details), name='profile_details'),
     # path('about/', views.about_finch, name='about'),

     # Htmx component calls
     path('c/listings/', views.ListingsHtmxView.as_view(), name='c_listings'),
     path('c/topics/', views.ForumTopicsHtmxView.as_view(), name='c_topics'),
     path('c/dancers/', views.DancersHtmxView.as_view(), name='c_dancers'),
     path('c/studios/', views.StudiosHtmxView.as_view(), name='c_studios'),
     path('c/creators/', views.CreatorsHtmxView.as_view(), name='c_creators'),

     # Ajax calls
     path('a/user/pwd_change/',
          login_required(views.user_password_update), name='user_pwd_change'),
     path('a/genres/',
          login_required(views.active_genres), name='active_genres'),
     path('a/my_studio_locations/',
          login_required(views.my_studio_locations), name='my_studio_locs'),

     path('a/my_studios_list/',
          login_required(views.my_studios_list), name='my_studios_list'),
     path('a/my_studios_details/',
          login_required(views.my_studio_details), name='my_studio_details'),

     path('a/studio/events/',
          login_required(views.list_studio_events), name='list_studio_events'),
     path('a/studio/event/create/',
          login_required(views.create_studio_event),
          name='create_studio_event'),
     path('a/studio/events/<int:pk>/',
          login_required(views.studio_event_details), name='studio_event_details'),

     path('a/events/list/',
          login_required(views.list_events), name='list_events'),
     path('a/events/studios/all/',
          login_required(views.list_all_studio_events),
          name='list_all_studio_events'),
     path('a/forum_topic/create/',
          login_required(views.create_forum_topic), name='create_forum_topic'),

    # Core Admin Dashboard
    path('adj-view/', views.AdminIndexView.as_view(), name='dcc_admin'),
    path('adj-view/verify-user-email', views.resend_verification_email, name='verify_user_email'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.MEDIA_URL and settings.MEDIA_URL.startswith("/core"):
    urlpatterns.append(
        re_path(r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL[5:].lstrip("/")),
        serve, kwargs={"document_root":settings.MEDIA_ROOT})
    )