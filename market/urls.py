from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='market/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Profile - IMPORTANT: Put 'edit' BEFORE '<str:username>'
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),  # Move this BEFORE username
    path('profile/<str:username>/', views.profile_view, name='profile_user'),  # This should be LAST
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),
    
    # Conversations & Messages
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/start/<int:product_pk>/', views.start_conversation, name='start_conversation'),
    
    # Ratings
    path('rate/<str:username>/', views.rate_seller, name='rate_seller'),
    
    # Recommendations
    path('recommendations/', views.recommendations, name='recommendations'),
]