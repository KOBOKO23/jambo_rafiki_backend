"""
Testimonial serializers
"""
from rest_framework import serializers
from .models import Testimonial


class TestimonialSubmitSerializer(serializers.ModelSerializer):
    """
    Public serializer — used when anyone submits a testimonial.
    Email is write-only so it never leaks in responses.
    """

    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Testimonial
        fields = [
            'id',
            'name',
            'email',
            'role',
            'role_custom',
            'text',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Testimonial cannot be empty")
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Testimonial must be at least 20 characters")
        return value.strip()

    def validate_role_custom(self, value):
        return value.strip()


class TestimonialPublicSerializer(serializers.ModelSerializer):
    """
    Public read serializer — only approved testimonials, no email exposed.
    display_role merges role_custom and role choice into one clean field.
    """

    display_role = serializers.CharField(read_only=True)

    class Meta:
        model = Testimonial
        fields = [
            'id',
            'name',
            'display_role',
            'text',
            'approved_at',
        ]


class TestimonialDetailSerializer(serializers.ModelSerializer):
    """
    Admin-only serializer — full detail including email, status, notes.
    """

    display_role = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Testimonial
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_at']