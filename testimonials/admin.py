"""
Testimonial admin configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_role', 'status_badge', 'created_at', 'approved_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['name', 'email', 'text']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'display_role']
    fieldsets = (
        ('Submitter', {
            'fields': ('name', 'email', 'role', 'role_custom', 'display_role')
        }),
        ('Testimonial', {
            'fields': ('text',)
        }),
        ('Moderation', {
            'fields': ('status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_selected', 'reject_selected']

    def status_badge(self, obj):
        colors = {
            'approved': 'green',
            'pending': 'orange',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_selected(self, request, queryset):
        count = 0
        for testimonial in queryset.filter(status='pending'):
            testimonial.approve()
            count += 1
        self.message_user(request, f'{count} testimonial(s) approved.')
    approve_selected.short_description = 'Approve selected testimonials'

    def reject_selected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} testimonial(s) rejected.')
    reject_selected.short_description = 'Reject selected testimonials'