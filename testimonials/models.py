"""
Testimonial models
"""
from django.db import models
from django.core.validators import EmailValidator


class Testimonial(models.Model):
    """Model for testimonials submitted by community members, volunteers, and supporters"""

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    ROLE_CHOICES = [
        ('community_member', 'Community Member'),
        ('volunteer', 'Volunteer'),
        ('donor', 'Donor'),
        ('sponsor', 'Sponsor'),
        ('partner', 'Partner Organisation'),
        ('other', 'Other'),
    ]

    # Submitter Information
    name = models.CharField(max_length=200, help_text="Full name of the person giving the testimonial")
    email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Email address (not displayed publicly)"
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='other',
        help_text="Relationship to Jambo Rafiki"
    )
    role_custom = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom role title to display (overrides role choice if set)"
    )

    # Testimonial Content
    text = models.TextField(help_text="The testimonial message")

    # Status — admin approves before it goes public
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Admin notes (not shown publicly)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-approved_at', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) - {self.get_status_display()}"

    @property
    def display_role(self):
        """Return custom role title if set, otherwise the readable choice label"""
        return self.role_custom if self.role_custom else self.get_role_display()

    def approve(self):
        from django.utils import timezone
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()