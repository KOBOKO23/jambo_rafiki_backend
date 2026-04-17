"""
Donation models
"""
import uuid

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, EmailValidator
from decimal import Decimal


class Donation(models.Model):
    """Model for donation records"""
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Credit/Debit Card (Stripe)'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    DONATION_TYPE_CHOICES = [
        ('one_time', 'One-time Donation'),
        ('monthly', 'Monthly Sponsorship'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    # Donor Information
    donor_name = models.CharField(max_length=200, help_text="Donor's full name")
    donor_email = models.EmailField(validators=[EmailValidator()], help_text="Donor's email")
    donor_phone = models.CharField(max_length=20, blank=True, help_text="Donor's phone number")
    is_anonymous = models.BooleanField(default=False, help_text="Keep donation anonymous")
    
    # Donation Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Donation amount"
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES')
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, default='one_time')
    purpose = models.CharField(max_length=300, blank=True, help_text="Purpose of donation")
    message = models.TextField(blank=True, help_text="Message from donor")
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=200, unique=True, help_text="Payment transaction ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # M-Pesa specific fields
    mpesa_receipt = models.CharField(max_length=100, blank=True)
    mpesa_phone = models.CharField(max_length=15, blank=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Stripe specific fields
    stripe_payment_intent = models.CharField(max_length=200, blank=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    
    # PayPal specific fields
    paypal_order_id = models.CharField(max_length=200, blank=True)
    
    # Receipt
    receipt_sent = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Admin notes")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['donor_email']),
            models.Index(fields=['payment_method', 'status', '-created_at']),
            models.Index(fields=['status', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.donor_name} - {self.currency} {self.amount} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Generate receipt number if completed"""
        if self.status == 'completed' and self.receipt_number in (None, ''):
            # Generate receipt number: JR-YYYY-MM-XXXX
            from django.utils import timezone
            now = timezone.now()
            unique = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"JR-{now.year}-{now.month:02d}-{unique}"
        
        super().save(*args, **kwargs)


class DonationCallback(models.Model):
    """Store raw callback data from payment gateways"""
    
    donation = models.ForeignKey(Donation, on_delete=models.SET_NULL, related_name='callbacks', null=True, blank=True)
    provider = models.CharField(max_length=20)  # mpesa, stripe, paypal
    external_id = models.CharField(max_length=200, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True)
    raw_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    requires_reconciliation = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    processing_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'external_id']),
            models.Index(fields=['provider', 'payload_hash']),
            models.Index(fields=['processed', '-created_at']),
            models.Index(fields=['requires_reconciliation', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'external_id'],
                condition=~Q(external_id=''),
                name='uniq_donationcallback_provider_external_id',
            ),
            models.UniqueConstraint(
                fields=['provider', 'payload_hash'],
                condition=~Q(payload_hash=''),
                name='uniq_donationcallback_provider_payload_hash',
            ),
        ]
    
    def __str__(self):
        return f"{self.provider} callback - {self.created_at}"
