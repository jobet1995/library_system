from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    CustomTokenObtainPairSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView


User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that extends the default JWT token obtain view.
    Returns access and refresh tokens for authentication.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    """
    View for user registration.
    Allows any user (authenticated or not) to create a new user account.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self.perform_create(serializer)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'User registered successfully'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve or update the authenticated user's profile.
    Only accessible by authenticated users.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.perform_update(serializer)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response(serializer.data, status=status.HTTP_200_OK)

class CheckAuthView(APIView):
    """
    Simple view to check if the user is authenticated.
    Returns the user's data if authenticated.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserDetailView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    View to list, create, retrieve, update or delete users.
    Only accessible by admin users.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = User.objects.all()
        # Add filtering if needed
        username = self.request.query_params.get('username')
        if username is not None:
            queryset = queryset.filter(username__icontains=username)
        return queryset
    
    def get_object(self):
        user_id = self.kwargs.get('pk')
        if user_id is not None:
            return get_object_or_404(User, id=user_id)
        return None
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Set password if provided
        password = self.request.data.get('password')
        if password:
            user.set_password(password)
            user.save()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance is None:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance is None:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Prevent users from deleting themselves
            if instance == request.user:
                return Response(
                    {'error': 'You cannot delete your own account'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            self.perform_destroy(instance)
            return Response(
                {'message': 'User deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# Home and dashboard views can be removed or kept for admin access
