from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('items/<uuid:item_id>/', views.item_detail, name='item_detail'),
    path('items/<uuid:item_id>/request/', views.create_request, name='create_request'),
    path('requests/<uuid:request_id>/approve/', views.approve_request, name='approve_request'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('items/<uuid:item_id>/delete/', views.delete_item, name='delete_item'),
    path('requests/<uuid:request_id>/decline/', views.decline_request, name='decline_request'),
    path('items/create/', views.create_item, name='create_item'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('items/<uuid:item_id>/chat/start/', views.start_chat, name='start_chat'),
    path('chats/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('inbox/', views.inbox, name='inbox'),
    path('request/<uuid:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('requests/<uuid:request_id>/return/', views.return_item, name='return_item'),
    path('requests/<uuid:request_id>/notify-return/', views.notify_return, name='notify_return'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),    
    path('delivery/<uuid:request_id>/', views.delivery_details, name='delivery_details'),
    path('return-success/<uuid:request_id>/', views.return_completed, name='return_completed'),
    path('requests/<uuid:request_id>/review/', views.leave_review, name='leave_review'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]