"""
Contact submission models
"""
from django.db import models
from django.core.validators import EmailValidator


class ContactSubmission(models.Model):
    """Model for contact form submissions"""
    
    name = models.CharField(max_length=200, help_text="Sender's full name")
    email = models.EmailField(validators=[EmailValidator()], help_text="Sender's email address")
    subject = models.CharField(max_length=300, help_text="Subject of the message")
    message = models.TextField(help_text="Message content")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False, help_text="Has this been read by admin?")
    notes = models.TextField(blank=True, help_text="Admin notes")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def mark_as_read(self):
        """Mark submission as read"""
        self.is_read = True
        self.save()
