from rest_framework import serializers
from django.conf import settings
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest

class ChildSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = [
            'id', 'first_name', 'last_name', 'age', 'gender',
            'bio', 'interests', 'photo', 'photo_url', 'is_sponsored', 'needs_sponsor'
        ]

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        url = obj.photo.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def validate_photo(self, value):
        max_size = getattr(settings, 'MAX_IMAGE_UPLOAD_SIZE', 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError('Photo file is too large.')

        content_type = getattr(value, 'content_type', '') or ''
        if content_type and not content_type.startswith('image/'):
            raise serializers.ValidationError('Only image uploads are allowed.')
        return value


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = '__all__'


class SponsorshipSerializer(serializers.ModelSerializer):
    child_name = serializers.SerializerMethodField()
    sponsor_name = serializers.CharField(source='sponsor.name', read_only=True)

    def get_child_name(self, obj):
        return str(obj.child)

    class Meta:
        model = Sponsorship
        fields = '__all__'


class SponsorshipInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorshipInterest
        fields = '__all__'
