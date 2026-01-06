"""
Contact serializers
"""
from rest_framework import serializers
from .models import ContactSubmission


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions"""
    
    class Meta:
        model = ContactSubmission
        fields = [
            'id',
            'name',
            'email',
            'subject',
            'message',
            'created_at',
            'is_read',
        ]
        read_only_fields = ['id', 'created_at', 'is_read']
    
    def validate_name(self, value):
        """Validate name is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_subject(self, value):
        """Validate subject is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Subject cannot be empty")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message is not empty and has minimum length"""
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long")
        return value.strip()


class ContactSubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for admin view"""
    
    class Meta:
        model = ContactSubmission
        fields = [
            'id',
            'name',
            'email',
            'subject',
            'message',
            'created_at',
            'updated_at',
            'is_read',
            'notes',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
