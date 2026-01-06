"""
Volunteer serializers
"""
from rest_framework import serializers
from .models import VolunteerApplication


class VolunteerApplicationSerializer(serializers.ModelSerializer):
    """Serializer for volunteer applications"""
    
    class Meta:
        model = VolunteerApplication
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'location',
            'skills',
            'availability',
            'duration',
            'motivation',
            'experience',
            'areas_of_interest',
            'created_at',
            'status',
        ]
        read_only_fields = ['id', 'created_at', 'status']
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_skills(self, value):
        if not value.strip():
            raise serializers.ValidationError("Please describe your skills")
        return value.strip()
    
    def validate_motivation(self, value):
        if not value.strip():
            raise serializers.ValidationError("Please tell us why you want to volunteer")
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Please provide more details (minimum 20 characters)")
        return value.strip()


class VolunteerApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for admin view"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = VolunteerApplication
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
