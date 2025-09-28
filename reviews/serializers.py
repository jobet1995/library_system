from rest_framework import serializers
from .models import Review, ReviewVote, ReviewReport
from django.utils.translation import gettext_lazy as _

class ReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ['id', 'user', 'vote_type', 'created_at']
        read_only_fields = ['user', 'created_at']
        extra_kwargs = {
            'user': {'required': False}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class ReviewReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReport
        fields = ['id', 'review', 'reporter', 'reason', 'description', 'status', 
                 'reviewed_by', 'reviewed_at', 'created_at']
        read_only_fields = ['reporter', 'status', 'reviewed_by', 'reviewed_at', 'created_at']
        extra_kwargs = {
            'reporter': {'required': False}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['reporter'] = request.user
        return super().create(validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    votes = ReviewVoteSerializer(many=True, read_only=True)
    reports = ReviewReportSerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_report = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'book', 'user', 'rating', 'title', 'content', 'is_approved',
            'created_at', 'updated_at', 'votes', 'reports', 'user_vote',
            'can_edit', 'can_delete', 'can_report', 'can_vote'
        ]
        read_only_fields = ['user', 'is_approved', 'created_at', 'updated_at']

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            return ReviewVoteSerializer(vote).data if vote else None
        return None

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.user == request.user or request.user.is_staff
        return False

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.user == request.user or request.user.is_staff
        return False

    def get_can_report(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user != request.user and not obj.reports.filter(reporter=request.user).exists()
        return False

    def get_can_vote(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user != request.user
        return False

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
            # Auto-approve reviews from staff
            if hasattr(request.user, 'is_staff') and request.user.is_staff:
                validated_data['is_approved'] = True
        return super().create(validated_data)
