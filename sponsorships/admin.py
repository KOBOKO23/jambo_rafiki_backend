from django.contrib import admin
from .models import Child, Sponsor, Sponsorship, SponsorshipInterest

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'age', 'gender', 'is_sponsored', 'needs_sponsor']
    list_filter = ['gender', 'is_sponsored', 'needs_sponsor']
    search_fields = ['first_name', 'last_name', 'bio']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']

@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ['sponsor', 'child', 'monthly_amount', 'currency', 'status', 'start_date']
    list_filter = ['status', 'currency', 'start_date']
    search_fields = ['sponsor__name', 'child__first_name', 'child__last_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SponsorshipInterest)
class SponsorshipInterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'preferred_level', 'created_at']
    list_filter = ['preferred_level', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']
