"""
Team member models (Optional - for dynamic team management)
Add to an appropriate app if needed
"""
from django.db import models


class TeamMember(models.Model):
    """Model for team members and leadership"""
    
    ROLE_CHOICES = [
        ('director', 'Executive Director'),
        ('board', 'Board Member'),
        ('staff', 'Staff Member'),
        ('volunteer', 'Volunteer Coordinator'),
    ]
    
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    title = models.CharField(max_length=200, help_text="e.g., Founder, Director, etc.")
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/', blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Social media (optional)
    linkedin = models.URLField(blank=True)
    
    # Display order
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
    
    def __str__(self):
        return f"{self.name} - {self.title}"
    
    @property
    def photo_url(self):
        """Get full photo URL"""
        if self.photo:
            return self.photo.url
        return None
