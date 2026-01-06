"""
Donation admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Donation, DonationCallback


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    """Admin interface for donations"""
    
    list_display = [
        'receipt_number',
        'donor_name',
        'amount_display',
        'payment_method',
        'status_badge',
        'created_at',
        'receipt_sent',
    ]
    
    list_filter = [
        'status',
        'payment_method',
        'currency',
        'donation_type',
        'receipt_sent',
        'created_at',
    ]
    
    search_fields = [
        'donor_name',
        'donor_email',
        'donor_phone',
        'transaction_id',
        'receipt_number',
        'mpesa_receipt',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'completed_at',
        'receipt_number',
    ]
    
    fieldsets = (
        ('Donor Information', {
            'fields': (
                'donor_name',
                'donor_email',
                'donor_phone',
                'is_anonymous',
            )
        }),
        ('Donation Details', {
            'fields': (
                'amount',
                'currency',
                'donation_type',
                'purpose',
                'message',
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method',
                'transaction_id',
                'status',
                'mpesa_receipt',
                'mpesa_phone',
                'stripe_payment_intent',
                'stripe_charge_id',
                'paypal_order_id',
            )
        }),
        ('Receipt', {
            'fields': (
                'receipt_number',
                'receipt_sent',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at',
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'send_receipts']
    
    def amount_display(self, obj):
        """Display amount with currency"""
        return f"{obj.currency} {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'processing': 'blue',
            'failed': 'red',
            'refunded': 'gray',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected donations as completed"""
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} donation(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def send_receipts(self, request, queryset):
        """Send receipts for completed donations"""
        from .views import DonationViewSet
        view = DonationViewSet()
        count = 0
        for donation in queryset.filter(status='completed', receipt_sent=False):
            view.send_donation_receipt(donation)
            count += 1
        self.message_user(request, f'Sent {count} receipt(s).')
    send_receipts.short_description = 'Send receipts'


@admin.register(DonationCallback)
class DonationCallbackAdmin(admin.ModelAdmin):
    """Admin interface for donation callbacks"""
    
    list_display = ['provider', 'donation', 'processed', 'created_at']
    list_filter = ['provider', 'processed', 'created_at']
    search_fields = ['raw_data']
    readonly_fields = ['created_at']
