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
]
