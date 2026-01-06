"""
Donation serializers
"""
from rest_framework import serializers
from .models import Donation, DonationCallback
from decimal import Decimal


class DonationSerializer(serializers.ModelSerializer):
    """Serializer for creating donations"""
    
    class Meta:
        model = Donation
        fields = [
            'id',
            'donor_name',
            'donor_email',
            'donor_phone',
            'is_anonymous',
            'amount',
            'currency',
            'donation_type',
            'purpose',
            'message',
            'payment_method',
            'created_at',
            'status',
        ]
        read_only_fields = ['id', 'created_at', 'status']
    
    def validate_amount(self, value):
        """Validate donation amount"""
        if value < Decimal('1.00'):
            raise serializers.ValidationError("Minimum donation amount is 1.00")
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError("Maximum donation amount is 1,000,000.00")
        return value
    
    def validate_donor_name(self, value):
        """Validate donor name"""
        if not value.strip():
            raise serializers.ValidationError("Donor name cannot be empty")
        return value.strip()


class MPesaDonationSerializer(serializers.Serializer):
    """Serializer for M-Pesa donation initiation"""
    
    donor_name = serializers.CharField(max_length=200)
    donor_email = serializers.EmailField()
    donor_phone = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1.00'))
    currency = serializers.CharField(max_length=3, default='KES')
    donation_type = serializers.CharField(max_length=20, default='one_time')
    purpose = serializers.CharField(max_length=300, required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(default=False)
    
    def validate_amount(self, value):
        """Validate M-Pesa amount (must be at least 1)"""
        if value < Decimal('1.00'):
            raise serializers.ValidationError("Minimum M-Pesa payment is KES 1")
        return value


class StripeDonationSerializer(serializers.Serializer):
    """Serializer for Stripe donation"""
    
    donor_name = serializers.CharField(max_length=200)
    donor_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1.00'))
    currency = serializers.CharField(max_length=3, default='USD')
    donation_type = serializers.CharField(max_length=20, default='one_time')
    purpose = serializers.CharField(max_length=300, required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(default=False)
    payment_method_id = serializers.CharField(max_length=200)  # From Stripe.js


class DonationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for admin view"""
    
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'receipt_number']


class DonationReceiptSerializer(serializers.ModelSerializer):
    """Serializer for donation receipts"""
    
    class Meta:
        model = Donation
        fields = [
            'receipt_number',
            'donor_name',
            'donor_email',
            'amount',
            'currency',
            'payment_method',
            'transaction_id',
            'created_at',
            'completed_at',
            'purpose',
        ]
