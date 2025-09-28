from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from books.models import Book


class Review(models.Model):
    """
    Model representing a book review by a user.
    """
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('book')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user')
    )
    
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 (poor) to 5 (excellent)')
    )
    
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('A brief title for your review')
    )
    
    content = models.TextField(
        _('review content'),
        help_text=_('Your detailed review of the book')
    )
    
    is_approved = models.BooleanField(
        _('is approved'),
        default=False,
        help_text=_('Whether this review has been approved by staff')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        unique_together = ['book', 'user']
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='rating_range'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username}'s review of {self.book.title}"
    
    def update_book_rating(self):
        """Update the book's average rating when a review is saved."""
        from django.db.models import Avg
        avg_rating = self.book.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        self.book.average_rating = round(avg_rating, 2) if avg_rating else None
        self.book.save(update_fields=['average_rating'])
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or self.rating_changed:
            self.update_book_rating()


class ReviewVote(models.Model):
    """
    Model for tracking upvotes and downvotes on reviews.
    """
    VOTE_TYPES = [
        ('up', _('Upvote')),
        ('down', _('Downvote')),
    ]
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name=_('review')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_votes',
        verbose_name=_('user')
    )
    
    vote_type = models.CharField(
        _('vote type'),
        max_length=4,
        choices=VOTE_TYPES
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('review vote')
        verbose_name_plural = _('review votes')
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.username} {self.get_vote_type_display()}d review by {self.review.user.username}"


class ReviewReport(models.Model):
    """
    Model for reporting inappropriate reviews.
    """
    REPORT_REASONS = [
        ('spam', _('Spam or advertising')),
        ('inappropriate', _('Inappropriate content')),
        ('hate_speech', _('Hate speech or offensive content')),
        ('wrong_info', _('Incorrect information')),
        ('other', _('Other reason')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('reviewed', _('Reviewed')),
        ('dismissed', _('Dismissed')),
    ]
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('review')
    )
    
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_reviews',
        verbose_name=_('reporter')
    )
    
    reason = models.CharField(
        _('reason'),
        max_length=20,
        choices=REPORT_REASONS
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Please provide details about why you are reporting this review')
    )
    
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        verbose_name=_('reviewed by')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    reviewed_at = models.DateTimeField(
        _('reviewed at'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('review report')
        verbose_name_plural = _('review reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report on review by {self.review.user.username}: {self.get_reason_display()}"
    
    def save(self, *args, **kwargs):
        if self.status == 'pending':
            self.reviewed_by = None
            self.reviewed_at = None
        elif self.status in ['reviewed', 'dismissed'] and not self.reviewed_at:
            from django.utils import timezone
            self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)
