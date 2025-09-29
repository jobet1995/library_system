from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

class UserModelTest(TestCase):
    """Test the User model and its methods"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'admin'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """Test user creation with required fields"""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))

    def test_create_superuser(self):
        """Test superuser creation"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        from .models import UserType
        self.assertEqual(admin_user.user_type, UserType.ADMIN)


class AuthenticationTests(TestCase):
    """Test authentication endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.token_url = reverse('accounts:token_obtain_pair')
        self.profile_url = reverse('accounts:user_profile')
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'  # This is okay as it's the string value of UserType.STUDENT
        }
        
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existingpass123',
            user_type='student'
        )

    def test_user_registration(self):
        """Test user registration with valid data"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        response_data = json.loads(response.content)
        self.assertIn('user', response_data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['user']['username'], self.user_data['username'])
        self.assertEqual(response_data['message'], 'User registered successfully')

    def test_user_login(self):
        """Test user login with valid credentials"""
        login_data = {
            'username': 'existinguser',
            'password': 'existingpass123'
        }
        response = self.client.post(
            self.token_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('access', response_data)
        self.assertIn('refresh', response_data)

        # Protected route testing is covered in other test methods


class UserProfileTests(TestCase):
    """Test user profile endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='student'
        )
        self.profile_url = reverse('accounts:user_profile')
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self.access_token}'

    def test_get_user_profile(self):
        """Test retrieving user profile"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['username'], self.user.username)
        self.assertEqual(response_data['email'], self.user.email)

    def test_update_user_profile(self):
        """Test updating user profile"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1234567890',
            'address': '123 Test St'
        }
        
        response = self.client.patch(
            self.profile_url,
            data=update_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Parse response data
        response_data = response.json()
        
        # Check response data (only check fields that are in the response)
        self.assertEqual(response_data['first_name'], 'Updated')
        self.assertEqual(response_data['last_name'], 'Name')
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Check database (all fields should be updated)
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone, '+1234567890')
        self.assertEqual(self.user.address, '123 Test St')
class AdminUserTests(TestCase):
    """Test admin-only user management endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='student'
        )
        self.users_list_url = reverse('accounts:user_list')
        self.user_detail_url = reverse('accounts:user_detail', args=[self.user.id])
        
        # Get admin JWT token
        refresh = RefreshToken.for_user(self.admin)
        self.access_token = str(refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self.access_token}'

    def test_list_users_as_admin(self):
        """Test admin can list all users"""
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_as_admin(self):
        """Test admin can update any user"""
        from .models import UserType
        
        # First, verify the initial user type is STUDENT
        self.assertEqual(self.user.user_type, UserType.STUDENT)
        
        # Prepare update data with the string value of UserType.STAFF
        update_data = {'user_type': 'staff'}  # Use string value instead of enum
        
        # Send the update request
        response = self.client.patch(
            self.user_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        if response.status_code != status.HTTP_200_OK:
            print(f"Response content: {response.content}")  # Debug output
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response data
        response_data = response.json()
        self.assertEqual(response_data['user_type'], 'staff')
        
        # Check database
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, UserType.STAFF)
        
        # Verify the user is no longer a student
        self.assertNotEqual(self.user.user_type, UserType.STUDENT)

    def test_delete_user_as_admin(self):
        """Test admin can delete users"""
        response = self.client.delete(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1)  # only admin remains
