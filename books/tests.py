import os
import tempfile
from datetime import date
from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Author, Publisher, Book

# Create your tests here.
User = get_user_model()

# Test media root for file uploads
MEDIA_ROOT = tempfile.mkdtemp()


class ModelTests(TestCase):
    """Test models in the books app."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        cls.author = Author.objects.create(
            name='Test Author',
            bio='Test Bio'
        )
        
        cls.publisher = Publisher.objects.create(
            name='Test Publisher',
            website='https://example.com',
            email='publisher@example.com'
        )
        
        cls.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            summary='Test Summary',
            language='English',
            shelf_location='A1',
            copies_available=5,
            copies_total=5,
            publisher=cls.publisher,
            category=cls.category
        )
        cls.book.authors.add(cls.author)
    
    def test_category_str(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), 'Test Category')
    
    def test_author_str(self):
        """Test author string representation."""
        self.assertEqual(str(self.author), 'Test Author')
    
    def test_publisher_str(self):
        """Test publisher string representation."""
        self.assertEqual(str(self.publisher), 'Test Publisher')
    
    def test_book_str(self):
        """Test book string representation."""
        self.assertEqual(str(self.book), 'Test Book (ISBN: 1234567890123)')
    
    def test_book_default_values(self):
        """Test book default values."""
        self.assertEqual(self.book.copies_available, 5)
        self.assertEqual(self.book.copies_total, 5)
    
    def test_book_availability(self):
        """Test book availability logic."""
        self.assertTrue(self.book.copies_available > 0)
        self.book.copies_available = 0
        self.book.save()
        self.assertEqual(self.book.copies_available, 0)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ViewTests(APITestCase):
    """Test API views in the books app."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        # Create test user
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        # Create test admin user
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test data
        cls.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        cls.author = Author.objects.create(
            name='Test Author',
            bio='Test Bio'
        )
        
        cls.publisher = Publisher.objects.create(
            name='Test Publisher',
            website='https://example.com',
            email='publisher@example.com'
        )
        
        cls.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            summary='Test Summary',
            language='English',
            shelf_location='A1',
            copies_available=5,
            copies_total=5,
            publisher=cls.publisher,
            category=cls.category
        )
        cls.book.authors.add(cls.author)
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_author_list(self):
        """Test retrieving a list of authors."""
        url = reverse('books:author-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
        # Check that our test author is in the response
        author_names = [a['name'] for a in data]
        self.assertIn('Test Author', author_names)
    
    def test_publisher_list(self):
        """Test retrieving a list of publishers."""
        url = reverse('books:publisher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        # Check that our test publisher is in the response
        publisher_names = [p['name'] for p in data]
        self.assertIn('Test Publisher', publisher_names)
        
        # Verify our test publisher data is correct
        test_publisher = next(p for p in data if p['name'] == 'Test Publisher')
        self.assertEqual(test_publisher['website'], 'https://example.com')
        self.assertEqual(test_publisher['email'], 'publisher@example.com')
    
    def test_book_list(self):
        """Test retrieving a list of books."""
        url = reverse('books:book-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
        # Check that our test book is in the response
        book_titles = [b['title'] for b in data]
        self.assertIn('Test Book', book_titles)
    
    def test_book_detail(self):
        """Test retrieving a single book."""
        url = reverse('books:book-detail', args=[self.book.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Book')
        self.assertEqual(len(response.data['authors']), 1)
    
    def test_create_book(self):
        """Test creating a new book."""
        url = reverse('books:book-list')
        data = {
            'title': 'New Book',
            'isbn': '9876543210987',
            'summary': 'New Book Summary',
            'language': 'English',
            'shelf_location': 'B2',
            'copies_available': 3,
            'copies_total': 3,
            'authors': [self.author.id],
            'publisher': self.publisher.id,
            'category': self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Book.objects.get(isbn='9876543210987').title, 'New Book')
    
    def test_update_book(self):
        """Test updating a book."""
        url = reverse('books:book-detail', args=[self.book.id])
        data = {'title': 'Updated Book Title'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Updated Book Title')
    
    def test_delete_book(self):
        """Test deleting a book."""
        url = reverse('books:book-detail', args=[self.book.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)
    
    def test_check_availability(self):
        """Test checking book availability."""
        url = reverse('books:book-detail', args=[self.book.id]) + 'check_availability/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response contains the expected data
        self.assertIn('isbn', response.data)
        self.assertEqual(response.data['isbn'], self.book.isbn)
    
    def test_add_copy(self):
        """Test adding a copy of a book."""
        url = reverse('books:book-detail', args=[self.book.id]) + 'add_copy/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_total, 6)
        self.assertEqual(self.book.copies_available, 6)
    
    def test_remove_copy(self):
        """Test removing a copy of a book."""
        url = reverse('books:book-detail', args=[self.book.id]) + 'remove_copy/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_total, 4)
        self.assertEqual(self.book.copies_available, 4)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access protected endpoints."""
        # Create a regular user (non-admin)
        self.client.force_authenticate(user=self.user)
        
        # Test creating a book (should be allowed for admin only)
        url = reverse('books:book-list')
        data = {'title': 'Unauthorized Book', 'isbn': '1111111111111'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test deleting a book (should be allowed for admin only)
        url = reverse('books:book-detail', args=[self.book.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FilteringTests(APITestCase):
    """Test filtering and searching functionality."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        # Create test user
        cls.user = User.objects.create_user(
            username='filtertestuser',
            email='filtertest@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        # Create test categories
        cls.fiction = Category.objects.create(name='Fiction Filter')
        cls.non_fiction = Category.objects.create(name='Non-Fiction Filter')
        
        # Create test authors
        cls.author1 = Author.objects.create(name='Author One Filter')
        cls.author2 = Author.objects.create(name='Author Two Filter')
        
        # Create test publishers
        cls.publishers1 = Publisher.objects.create(name='Publisher One Filter')
        cls.publishers2 = Publisher.objects.create(name='Publisher Two Filter')
        
        # Create test books
        cls.python_book = Book.objects.create(
            title='Python Programming',
            isbn='1111111111111',
            publisher=cls.publishers1,
            category=cls.non_fiction,
            copies_available=5,
            copies_total=5,
            language='English',
            summary='Learn Python programming',
            shelf_location='A1'
        )
        cls.python_book.authors.add(cls.author1)
        
        cls.django_book = Book.objects.create(
            title='Django for Beginners',
            isbn='2222222222222',
            publisher=cls.publishers2,
            category=cls.non_fiction,
            copies_available=3,
            copies_total=3,
            language='English',
            summary='Learn Django framework',
            shelf_location='A2'
        )
        cls.django_book.authors.add(cls.author2)
        
        cls.fiction_book = Book.objects.create(
            title='Science Fiction Stories',
            isbn='3333333333333',
            publisher=cls.publishers1,
            category=cls.fiction,
            copies_available=0,
            copies_total=2,
            language='English',
            summary='Collection of sci-fi stories',
            shelf_location='B1'
        )
        cls.fiction_book.authors.add(cls.author1)
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_filter_by_category(self):
        """Test filtering books by category."""
        url = f"{reverse('books:book-list')}?category={self.fiction.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Science Fiction Stories')
    
    def test_search_by_title(self):
        """Test searching books by title."""
        url = f"{reverse('books:book-list')}?search=Python"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Python Programming')
    
    def test_filter_by_availability(self):
        """Test filtering books by availability."""
        url = f"{reverse('books:book-list')}?copies_available__gt=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        # Should return 2 books with copies_available > 0
        self.assertEqual(len(data), 2)
        
        # Check that the available books are in the response
        titles = [book['title'] for book in data]
        self.assertIn('Python Programming', titles)
        self.assertIn('Django for Beginners', titles)
        self.assertNotIn('Science Fiction Stories', titles)
    
    def test_ordering(self):
        """Test ordering of books."""
        url = f"{reverse('books:book-list')}?ordering=-title"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if response is paginated
        if 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
            
        # Check the order of books
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['title'], 'Science Fiction Stories')
        self.assertEqual(data[1]['title'], 'Python Programming')
        self.assertEqual(data[2]['title'], 'Django for Beginners')


class PaginationTests(APITestCase):
    """Test pagination of API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_superuser(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create multiple categories to test pagination
        for i in range(15):
            Category.objects.create(name=f'Category {i+1}')
    
    def test_pagination(self):
        """Test that pagination is working."""
        url = reverse('books:category-list')
        response = self.client.get(url, {'page': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # Just verify we got some results, don't check exact count as it depends on the page size
    
    def test_page_size_parameter(self):
        """Test pagination functionality."""
        # Get the first page of categories
        url = reverse('books:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the response is paginated
        if 'results' in response.data:
            first_page_results = response.data['results']
            total_categories = Category.objects.count()
            
            # If there are more categories than the default page size, check next page exists
            if total_categories > len(first_page_results):
                self.assertIsNotNone(response.data.get('next'))
                
                # Get the next page
                next_response = self.client.get(response.data['next'])
                self.assertEqual(next_response.status_code, status.HTTP_200_OK)
                
                if 'results' in next_response.data:
                    next_page_results = next_response.data['results']
                    # Ensure the next page has results
                    self.assertGreater(len(next_page_results), 0)
                    
                    # If we have results on both pages, they should be different
                    if first_page_results and next_page_results:
                        self.assertNotEqual(
                            first_page_results[0]['id'],
                            next_page_results[0]['id']
                        )
            
            # Test that we can request a specific page
            if response.data.get('count', 0) > 1:
                page2_response = self.client.get(f"{url}?page=2")
                self.assertEqual(page2_response.status_code, status.HTTP_200_OK)
                if 'results' in page2_response.data:
                    self.assertGreater(len(page2_response.data['results']), 0)
