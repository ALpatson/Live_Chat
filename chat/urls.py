from django.urls import path, include
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('rooms/', views.rooms, name='rooms'),
    path('create-room/', views.create_room, name='create_room'),
    path('room/<str:pk>/', views.room, name='room'),
    path('room-detail/<str:pk>/', views.room_detail, name='room_detail'),
    path('request-join/<str:pk>/', views.request_join, name='request_join'),
    path('room-requests/<str:pk>/', views.room_requests, name='room_requests'),
    path('approve-request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('get-pending-count/<str:room_name>/', views.get_pending_count, name='get_pending_count'),
    path('getMessages/<str:room_name>/', views.getMessages, name='getMessages'),
    path('send', views.send, name='send'),
]
