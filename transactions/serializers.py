from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import BorrowTransaction, Fine
from books.serializers import BookSerializer
from accounts.serializers import UserSerializer


class FineSerializer(serializers.ModelSerializer):
    """
    Serializer for the Fine model.
    """
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Fine
        fields = [
            'id', 'amount', 'paid', 'created_at', 'paid_at', 
            'status', 'transaction'
        ]
        read_only_fields = ['id', 'created_at', 'status']
    
    def get_status(self, obj):
        """Get human-readable status of the fine."""
        return obj.get_status_display()
    
    def validate(self, data):
        """
        Validate the fine data.
        - Ensure paid_at is set when marking as paid
        - Ensure amount is positive
        """
        if 'paid' in data and data['paid'] and 'paid_at' not in data:
            data['paid_at'] = timezone.now()
        
        if 'amount' in data and data['amount'] < 0:
            raise serializers.ValidationError({
                'amount': _('Fine amount cannot be negative.')
            })
            
        return data


class BorrowTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for the BorrowTransaction model.
    Includes nested book and user details.
    """
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    fine_record = FineSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    can_renew = serializers.SerializerMethodField()
    
    class Meta:
        model = BorrowTransaction
        fields = [
            'id', 'book', 'user', 'borrow_date', 'due_date', 'return_date',
            'is_returned', 'fine', 'renew_count', 'notes', 'fine_record',
            'status', 'days_remaining', 'can_renew'
        ]
        read_only_fields = [
            'id', 'fine', 'renew_count', 'fine_record', 'status',
            'days_remaining', 'can_renew'
        ]
    
    def get_status(self, obj):
        """Get human-readable status of the transaction."""
        if obj.is_returned:
            return _('Returned')
        if obj.due_date < timezone.now().date():
            return _('Overdue')
        return _('On loan')
    
    def get_days_remaining(self, obj):
        """Get days remaining until due or days overdue."""
        if obj.is_returned:
            return 0
        
        today = timezone.now().date()
        delta = (obj.due_date - today).days
        return delta
    
    def get_can_renew(self, obj):
        """Check if the book can be renewed."""
        if obj.is_returned:
            return False
        
        from django.conf import settings
        return obj.renew_count < settings.LIBRARY_SETTINGS['MAX_RENEWALS']
    
    def validate(self, data):
        """
        Validate the transaction data.
        - Ensure return_date is after borrow_date
        - Ensure due_date is after borrow_date
        """
        if 'return_date' in data and 'borrow_date' in data:
            if data['return_date'] < data['borrow_date']:
                raise serializers.ValidationError({
                    'return_date': _('Return date cannot be before borrow date.')
                })
        
        if 'due_date' in data and 'borrow_date' in data:
            if data['due_date'] < data['borrow_date']:
                raise serializers.ValidationError({
                    'due_date': _('Due date cannot be before borrow date.')
                })
        
        return data


class BorrowBookSerializer(serializers.Serializer):
    """
    Serializer for borrowing a book.
    """
    book_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)
    due_date = serializers.DateField(required=False)
    
    def validate_book_id(self, value):
        """Validate that the book exists and is available."""
        from books.models import Book
        try:
            book = Book.objects.get(pk=value)
            if book.copies_available <= 0:
                raise serializers.ValidationError(
                    _('This book is currently not available.')
                )
            return value
        except Book.DoesNotExist:
            raise serializers.ValidationError(_('Book not found.'))
    
    def validate_user_id(self, value):
        """Validate that the user exists."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_('User not found.'))
    
    def create(self, validated_data):
        """Create a new borrow transaction."""
        from books.models import Book
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        book = Book.objects.get(pk=validated_data['book_id'])
        user = validated_data['user_id']  # Already a User instance from validate_user_id
        
        # Create the transaction
        transaction = BorrowTransaction.objects.create(
            book=book,
            user=user,
            due_date=validated_data.get('due_date')  # Will use default if not provided
        )
        
        return transaction


class ReturnBookSerializer(serializers.Serializer):
    """
    Serializer for returning a borrowed book.
    """
    transaction_id = serializers.IntegerField(required=True)
    
    def validate_transaction_id(self, value):
        """Validate that the transaction exists and is active."""
        try:
            transaction = BorrowTransaction.objects.get(
                pk=value,
                is_returned=False
            )
            return transaction
        except BorrowTransaction.DoesNotExist:
            raise serializers.ValidationError(
                _('Active borrow transaction not found.')
            )
    
    def create(self, validated_data):
        """Mark the book as returned and calculate any fines."""
        transaction = validated_data['transaction_id']  # Already a BorrowTransaction instance
        
        # Update the transaction
        transaction.return_date = timezone.now().date()
        transaction.is_returned = True
        transaction.fine = transaction.calculate_fine()
        transaction.save()
        
        return transaction


class RenewBookSerializer(serializers.Serializer):
    """
    Serializer for renewing a book loan.
    """
    transaction_id = serializers.IntegerField(required=True)
    
    def validate_transaction_id(self, value):
        """Validate that the transaction exists and can be renewed."""
        try:
            transaction = BorrowTransaction.objects.get(
                pk=value,
                is_returned=False
            )
            
            # Check if already at max renewals
            from django.conf import settings
            if transaction.renew_count >= settings.LIBRARY_SETTINGS['MAX_RENEWALS']:
                raise serializers.ValidationError(
                    _('Maximum number of renewals reached.')
                )
                
            return transaction
            
        except BorrowTransaction.DoesNotExist:
            raise serializers.ValidationError(
                _('Active borrow transaction not found.')
            )
    
    def create(self, validated_data):
        """Renew the book loan."""
        transaction = validated_data['transaction_id']  # Already a BorrowTransaction instance
        success, message = transaction.renew()
        
        if not success:
            raise serializers.ValidationError(message)
            
        return transaction
