from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticates against both username and email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
            
        try:
            # Try to fetch the user by searching the username or email field
            user = UserModel._default_manager.get(
                Q(username__iexact=username) | 
                Q(email__iexact=username)
            )
            
            if user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            UserModel().set_password(password)


class LibraryStaffBackend(ModelBackend):
    """
    Custom backend to handle library staff authentication.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        try:
            user = UserModel._default_manager.get(
                Q(username__iexact=username) | 
                Q(email__iexact=username),
                is_active=True,
                is_staff=True
            )
            
            if user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            UserModel().set_password(password)


class LibraryAdminBackend(ModelBackend):
    """
    Custom backend to handle library admin authentication.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        try:
            user = UserModel._default_manager.get(
                Q(username__iexact=username) | 
                Q(email__iexact=username),
                is_active=True,
                is_superuser=True
            )
            
            if user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            UserModel().set_password(password)


class BranchSpecificBackend(ModelBackend):
    """
    Custom backend to handle branch-specific authentication.
    Users can only log in if they are assigned to the specified branch.
    """
    def authenticate(self, request, username=None, password=None, branch_id=None, **kwargs):
        UserModel = get_user_model()
        
        if not branch_id:
            return None
            
        try:
            user = UserModel._default_manager.get(
                Q(username__iexact=username) | 
                Q(email__iexact=username),
                is_active=True,
                branch__id=branch_id
            )
            
            if user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            UserModel().set_password(password)
