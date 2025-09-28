from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils.translation import gettext_lazy as _

from .models import BorrowTransaction, Fine
from .serializers import (
    BorrowTransactionSerializer,
    FineSerializer,
    BorrowBookSerializer,
    ReturnBookSerializer,
    RenewBookSerializer
)


class BorrowTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing book borrow transactions.
    """
    queryset = BorrowTransaction.objects.all()
    serializer_class = BorrowTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'book', 'is_returned', 'borrow_date', 'due_date']
    search_fields = ['book__title', 'book__isbn', 'user__username', 'user__email']
    ordering_fields = ['borrow_date', 'due_date', 'return_date']

    def get_queryset(self):
        """
        Filter transactions based on user permissions.
        Regular users can only see their own transactions.
        Staff can see all transactions.
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset.select_related('book', 'user', 'fine_record')

    def get_permissions(self):
        """
        Only allow staff to create, update, or delete transactions.
        Regular users can only view their own transactions.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def borrow(self, request):
        """
        Endpoint for borrowing a book.
        """
        serializer = BorrowBookSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            return Response(
                BorrowTransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def return_book(self, request):
        """
        Endpoint for returning a borrowed book.
        """
        serializer = ReturnBookSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            return Response(
                BorrowTransactionSerializer(transaction).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Endpoint for renewing a book loan.
        """
        transaction = self.get_object()
        
        # Regular users can only renew their own loans
        if not request.user.is_staff and transaction.user != request.user:
            return Response(
                {'detail': _('You can only renew your own loans.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RenewBookSerializer(data={'transaction_id': transaction.id})
        if serializer.is_valid():
            transaction = serializer.save()
            return Response(
                BorrowTransactionSerializer(transaction).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def fine(self, request, pk=None):
        """
        Get the fine for a specific transaction.
        """
        transaction = self.get_object()
        
        # Regular users can only see their own fines
        if not request.user.is_staff and transaction.user != request.user:
            return Response(
                {'detail': _('Not found.')},  # Don't leak information
                status=status.HTTP_404_NOT_FOUND
            )
        
        fine, created = Fine.objects.get_or_create(
            transaction=transaction,
            defaults={'user': transaction.user, 'amount': transaction.fine}
        )
        
        serializer = FineSerializer(fine)
        return Response(serializer.data)


class FineViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    """
    API endpoint for managing fines.
    """
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'paid', 'transaction']
    search_fields = ['user__username', 'user__email', 'transaction__book__title']
    ordering_fields = ['created_at', 'paid_at', 'amount']

    def get_queryset(self):
        """
        Filter fines based on user permissions.
        Regular users can only see their own fines.
        Staff can see all fines.
        """
        queryset = Fine.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset.select_related('user', 'transaction', 'transaction__book')

    def get_permissions(self):
        """
        Only allow staff to update fines.
        Regular users can only view their own fines.
        """
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def pay(self, request, pk=None):
        """
        Mark a fine as paid.
        """
        fine = self.get_object()
        if fine.paid:
            return Response(
                {'detail': _('This fine has already been paid.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fine.mark_as_paid()
        return Response(
            FineSerializer(fine).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def total_unpaid(self, request):
        """
        Get the total amount of unpaid fines for the current user.
        """
        if request.user.is_staff:
            total = Fine.objects.filter(paid=False).aggregate(total=models.Sum('amount'))['total'] or 0
        else:
            total = Fine.objects.filter(user=request.user, paid=False).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
        
        return Response({'total_unpaid': total})
