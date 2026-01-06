"""
Volunteer admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import VolunteerApplication


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    """Admin interface for volunteer applications"""
    
    list_display = [
        'name',
        'email',
        'phone',
        'location',
        'status_badge',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'email',
        'phone',
        'skills',
        'motivation',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'name',
                'email',
                'phone',
                'location',
            )
        }),
        ('Volunteer Details', {
            'fields': (
                'skills',
                'availability',
                'duration',
                'motivation',
                'experience',
                'areas_of_interest',
            )
        }),
        ('Application Status', {
            'fields': (
                'status',
                'notes',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'reviewed_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_approved', 'mark_as_contacted']
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'approved': 'green',
            'pending': 'orange',
            'reviewing': 'blue',
            'rejected': 'red',
            'contacted': 'purple',
            'scheduled': 'teal',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_approved(self, request, queryset):
        """Mark selected applications as approved"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} application(s) approved.')
    mark_as_approved.short_description = 'Approve selected'
    
    def mark_as_contacted(self, request, queryset):
        """Mark selected applications as contacted"""
        updated = queryset.update(status='contacted')
        self.message_user(request, f'{updated} application(s) marked as contacted.')
    mark_as_contacted.short_description = 'Mark as contacted'
