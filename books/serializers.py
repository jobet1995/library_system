from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Category, Author, Publisher, Book


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for the Author model."""
    book_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'book_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'book_count', 'created_at', 'updated_at']


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for the Publisher model."""
    book_count = serializers.IntegerField(read_only=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'website', 'email', 'book_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'book_count', 'created_at', 'updated_at']


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing books."""
    authors = serializers.StringRelatedField(many=True)
    publisher = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'authors', 'publisher', 'category',
            'publication_date', 'copies_available', 'copies_total',
            'cover_image', 'language', 'shelf_location'
        ]
        read_only_fields = ['id', 'copies_available']


class BookDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual book view."""
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'summary', 'authors', 'publisher', 
            'category', 'publication_date', 'copies_available', 
            'copies_total', 'cover_image', 'cover_image_url', 'language', 
            'shelf_location', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'copies_available', 'is_available', 'created_at', 'updated_at'
        ]
    
    def get_cover_image_url(self, obj):
        """Return the full URL of the cover image if it exists."""
        if obj.cover_image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating books."""
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        required=True
    )
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        required=False,
        allow_null=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'summary', 'authors', 'publisher', 'category',
            'publication_date', 'copies_total', 'cover_image', 'language',
            'shelf_location'
        ]
    
    def validate_copies_total(self, value):
        """Ensure copies_total is not negative."""
        if value < 0:
            raise serializers.ValidationError(_("Number of copies cannot be negative."))
        return value
    
    def create(self, validated_data):
        """Create a new book with the given validated data."""
        authors_data = validated_data.pop('authors', [])
        book = Book.objects.create(**validated_data)
        book.authors.set(authors_data)
        return book
    
    def update(self, instance, validated_data):
        """Update a book instance with the given validated data."""
        authors_data = validated_data.pop('authors', None)
        
        # Update all fields except authors
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update authors if provided
        if authors_data is not None:
            instance.authors.set(authors_data)
        
        instance.save()
        return instance
