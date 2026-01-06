"""
Volunteer application models
"""
from django.db import models
from django.core.validators import EmailValidator


class VolunteerApplication(models.Model):
    """Model for volunteer applications"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('contacted', 'Contacted'),
        ('scheduled', 'Scheduled'),
    ]
    
    # Personal Information
    name = models.CharField(max_length=200, help_text="Full name")
    email = models.EmailField(validators=[EmailValidator()], help_text="Email address")
    phone = models.CharField(max_length=20, help_text="Phone number")
    location = models.CharField(max_length=200, help_text="City/Country")
    
    # Volunteer Details
    skills = models.TextField(help_text="Skills and expertise")
    availability = models.CharField(max_length=500, help_text="When are you available?")
    duration = models.CharField(max_length=200, help_text="How long can you volunteer?")
    motivation = models.TextField(help_text="Why do you want to volunteer with us?")
    experience = models.TextField(blank=True, help_text="Previous volunteer experience")
    
    # Preferences
    areas_of_interest = models.TextField(
        blank=True,
        help_text="Which programs interest you? (Education, Health, etc.)"
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Admin notes")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Volunteer Application'
        verbose_name_plural = 'Volunteer Applications'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
