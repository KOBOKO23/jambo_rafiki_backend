from rest_framework import serializers
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest

class ChildSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()

    class Meta:
        model = Child
        fields = [
            'id', 'first_name', 'last_name', 'age', 'gender',
            'bio', 'interests', 'photo', 'is_sponsored', 'needs_sponsor'
        ]


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = '__all__'


class SponsorshipSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source='child.__str__', read_only=True)
    sponsor_name = serializers.CharField(source='sponsor.name', read_only=True)

    class Meta:
        model = Sponsorship
        fields = '__all__'


class SponsorshipInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorshipInterest
        fields = '__all__'
