"""
Newsletter serializers
"""
from rest_framework import serializers
from .models import NewsletterSubscriber


class NewsletterSubscribeSerializer(serializers.Serializer):
    """Serializer for newsletter subscription"""
    
    email = serializers.EmailField()
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    source = serializers.CharField(max_length=100, required=False, allow_blank=True)


class NewsletterUnsubscribeSerializer(serializers.Serializer):
    """Serializer for newsletter unsubscription"""
    
    email = serializers.EmailField()


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serializer for newsletter subscribers (admin)"""
    
    class Meta:
        model = NewsletterSubscriber
        fields = '__all__'
        read_only_fields = ['subscribed_at', 'unsubscribed_at']
