"""
Newsletter admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin interface for newsletter subscribers"""
    
    list_display = [
        'email',
        'name',
        'status_badge',
        'subscribed_at',
        'source',
    ]
    
    list_filter = [
        'is_active',
        'subscribed_at',
        'source',
    ]
    
    search_fields = [
        'email',
        'name',
    ]
    
    readonly_fields = [
        'subscribed_at',
        'unsubscribed_at',
    ]
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': (
                'email',
                'name',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'source',
            )
        }),
        ('Metadata', {
            'fields': (
                'subscribed_at',
                'unsubscribed_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'export_emails']
    
    def status_badge(self, obj):
        """Display status with color badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers"""
        updated = queryset.update(is_active=True, unsubscribed_at=None)
        self.message_user(request, f'{updated} subscriber(s) activated.')
    activate_subscribers.short_description = 'Activate selected'
    
    def deactivate_subscribers(self, request, queryset):
        """Deactivate selected subscribers"""
        from django.utils import timezone
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscriber(s) deactivated.')
    deactivate_subscribers.short_description = 'Deactivate selected'
    
    def export_emails(self, request, queryset):
        """Export emails as comma-separated list"""
        emails = ', '.join(queryset.values_list('email', flat=True))
        self.message_user(request, f'Emails: {emails}')
    export_emails.short_description = 'Export emails'
