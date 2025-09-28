from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('check-auth/', views.CheckAuthView.as_view(), name='check_auth'),
    
    # Admin-only user management endpoints
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/', views.UserDetailView.as_view(), name='user_list'),
]
