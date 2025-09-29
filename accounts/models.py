from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import uuid


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""
    
    def _create_user(self, username, email, password, **extra_fields):
        """Create and save a user with the given username, email, and password."""
        if not username:
            raise ValueError('The username must be set')
        if not email:
            raise ValueError('The email must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('user_type', 'student')
        return self._create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(username, email, password, **extra_fields)


class UserType(models.TextChoices):
    ADMIN = 'admin', _('Administrator')
    LIBRARIAN = 'librarian', _('Librarian')
    STAFF = 'staff', _('Staff')
    STUDENT = 'student', _('Student')


class Gender(models.TextChoices):
    MALE = 'M', _('Male')
    FEMALE = 'F', _('Female')
    OTHER = 'O', _('Other')
    PREFER_NOT_TO_SAY = 'N', _('Prefer not to say')


class CustomUser(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    Adds additional fields for user profiles in the library system.
    """
    objects = CustomUserManager()
    user_type = models.CharField(
        _('user type'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.STUDENT,
        help_text=_('Designates the type of user')
    )
    
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('User\'s contact phone number')
    )
    
    address = models.TextField(
        _('address'),
        blank=True,
        null=True,
        help_text=_('User\'s physical address')
    )
    
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
        help_text=_('User\'s date of birth')
    )
    
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text=_('User\'s profile picture')
    )
    
    gender = models.CharField(
        _('gender'),
        max_length=1,
        choices=Gender.choices,
        blank=True,
        null=True,
        help_text=_('User\'s gender')
    )
    
    membership_id = models.UUIDField(
        _('membership ID'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Unique membership identifier for the user')
    )
    
    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Department or faculty the user belongs to')
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['username']
        indexes = [
            models.Index(fields=['username'], name='username_idx'),
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['user_type'], name='user_type_idx'),
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username

    def is_librarian(self):
        """Check if the user is a librarian."""
        return self.user_type == UserType.LIBRARIAN

    def is_staff_member(self):
        """Check if the user is a staff member."""
        return self.user_type == UserType.STAFF

    def is_student(self):
        return self.user_type == UserType.STUDENT
    def is_admin(self):
        """Check if the user is an admin."""
        return self.user_type == UserType.ADMIN
        
