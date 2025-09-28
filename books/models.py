from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Model representing a book category.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Enter a book category (e.g. Science Fiction, Mystery, Programming)')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_('Optional description of the category')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('The date and time when this category was created')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('The date and time when this category was last updated')
    )
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
    
    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Author(models.Model):
    """
    Model representing a book author.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_("The author's full name")
    )
    
    bio = models.TextField(
        _('biography'),
        blank=True,
        null=True,
        help_text=_("A short biography of the author")
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('The date and time when this author was added')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('The date and time when this author was last updated')
    )
    
    class Meta:
        verbose_name = _('Author')
        verbose_name_plural = _('Authors')
        ordering = ['name']
    
    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Publisher(models.Model):
    """
    Model representing a book publisher.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_("The publisher's name")
    )
    
    website = models.URLField(
        _('website'),
        blank=True,
        null=True,
        help_text=_("The publisher's website URL")
    )
    
    email = models.EmailField(
        _('email'),
        blank=True,
        null=True,
        help_text=_("The publisher's contact email")
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('The date and time when this publisher was added')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('The date and time when this publisher was last updated')
    )
    
    class Meta:
        verbose_name = _('Publisher')
        verbose_name_plural = _('Publishers')
        ordering = ['name']
    
    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Book(models.Model):
    """
    Model representing a book in the library.
    """
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('The title of the book')
    )
    
    isbn = models.CharField(
        _('ISBN'),
        max_length=20,
        unique=True,
        help_text=_('International Standard Book Number (unique)')
    )
    
    cover_image = models.ImageField(
        _('cover image'),
        upload_to='book_covers/',
        null=True,
        blank=True,
        help_text=_('Cover image of the book')
    )
    
    summary = models.TextField(
        _('summary'),
        blank=True,
        null=True,
        help_text=_('A brief summary or description of the book')
    )
    
    language = models.CharField(
        _('language'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Language the book is written in')
    )
    
    shelf_location = models.CharField(
        _('shelf location'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Physical location of the book in the library')
    )
    
    authors = models.ManyToManyField(
        Author,
        related_name='books',
        verbose_name=_('authors'),
        help_text=_('The authors of this book')
    )
    
    publisher = models.ForeignKey(
        'Publisher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name=_('publisher'),
        help_text=_('The publisher of this book')
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name=_('category'),
        help_text=_('The category this book belongs to')
    )
    
    publication_date = models.DateField(
        _('publication date'),
        null=True,
        blank=True,
        help_text=_('The date when this book was published')
    )
    
    copies_total = models.PositiveIntegerField(
        _('total copies'),
        default=1,
        help_text=_('Total number of copies available in the library')
    )
    
    copies_available = models.PositiveIntegerField(
        _('available copies'),
        default=1,
        help_text=_('Number of copies currently available for checkout')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('The date and time when this book was added')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('The date and time when this book was last updated')
    )
    
    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')
        ordering = ['title', 'publication_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['isbn']),
            models.Index(fields=['publication_date']),
        ]
    
    def __str__(self):
        """String for representing the Model object."""
        return f"{self.title} (ISBN: {self.isbn})"
    
    def save(self, *args, **kwargs):
        """Override save to ensure copies_available doesn't exceed copies_total."""
        if self.copies_available > self.copies_total:
            self.copies_available = self.copies_total
        super().save(*args, **kwargs)
