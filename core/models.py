from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BackgroundJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    job_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    available_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'available_at']),
            models.Index(fields=['job_type', 'status']),
        ]

    def __str__(self):
        return f"{self.job_type} ({self.status})"


class AuditEvent(models.Model):
    """Immutable log of security/operationally sensitive transitions."""

    event_type = models.CharField(max_length=100)
    actor = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
    )
    source = models.CharField(max_length=100, blank=True)
    target_model = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.target_model}:{self.target_id})"


class SiteSetting(models.Model):
    """Singleton site settings managed by the CMS."""

    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    site_name = models.CharField(max_length=200, default='Jambo Rafiki')
    tagline = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True)
    favicon = models.ImageField(upload_to='site/', blank=True)
    primary_color = models.CharField(max_length=32, blank=True)
    secondary_color = models.CharField(max_length=32, blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    seo_default_title = models.CharField(max_length=255, blank=True)
    seo_default_description = models.TextField(blank=True)
    homepage_title = models.CharField(max_length=255, blank=True)
    homepage_subtitle = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.site_name or 'Site settings'


class Page(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_REVIEW = 'review'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_REVIEW, 'In Review'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    template = models.CharField(max_length=100, default='default', blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    sort_order = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_pages')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_pages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']
        indexes = [
            models.Index(fields=['status', '-updated_at']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PageSection(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    cta_label = models.CharField(max_length=120, blank=True)
    cta_url = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='page-sections/', blank=True)
    settings = models.JSONField(default=dict, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['page', 'is_active', 'sort_order']),
        ]

    def __str__(self):
        return f'{self.page.title} - {self.section_type}'


class NavigationMenu(models.Model):
    LOCATION_HEADER = 'header'
    LOCATION_FOOTER = 'footer'
    LOCATION_UTILITY = 'utility'

    LOCATION_CHOICES = [
        (LOCATION_HEADER, 'Header'),
        (LOCATION_FOOTER, 'Footer'),
        (LOCATION_UTILITY, 'Utility'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default=LOCATION_HEADER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['location', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class NavigationMenuItem(models.Model):
    menu = models.ForeignKey(NavigationMenu, on_delete=models.CASCADE, related_name='items')
    label = models.CharField(max_length=120)
    page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='menu_items')
    url = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['menu', 'sort_order', 'id']
        indexes = [
            models.Index(fields=['menu', 'is_active', 'sort_order']),
        ]

    def __str__(self):
        return f'{self.menu.name} - {self.label}'


class Banner(models.Model):
    PLACEMENT_HERO = 'hero'
    PLACEMENT_ANNOUNCEMENT = 'announcement'

    PLACEMENT_CHOICES = [
        (PLACEMENT_HERO, 'Hero'),
        (PLACEMENT_ANNOUNCEMENT, 'Announcement'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    cta_label = models.CharField(max_length=120, blank=True)
    cta_url = models.CharField(max_length=255, blank=True)
    placement = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default=PLACEMENT_HERO)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-updated_at']
        indexes = [
            models.Index(fields=['placement', 'is_active', '-priority']),
        ]

    def __str__(self):
        return self.title


class RedirectRule(models.Model):
    STATUS_301 = 301
    STATUS_302 = 302

    STATUS_CODE_CHOICES = [
        (STATUS_301, '301 Permanent Redirect'),
        (STATUS_302, '302 Temporary Redirect'),
    ]

    source_path = models.CharField(max_length=255, unique=True)
    target_url = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField(choices=STATUS_CODE_CHOICES, default=STATUS_301)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['source_path']
        indexes = [
            models.Index(fields=['is_active', 'source_path']),
        ]

    def __str__(self):
        return f'{self.source_path} -> {self.target_url}'


class MediaAsset(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='media-assets/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True)
    tags = models.JSONField(default=list, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    size = models.PositiveIntegerField(default=0)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentRevision(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=64)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='content_revisions')
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='published_revisions')
    summary = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id', '-version']),
            models.Index(fields=['status', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['entity_type', 'entity_id', 'version'], name='uniq_content_revision_entity_version'),
        ]

    def __str__(self):
        return f'{self.entity_type}:{self.entity_id} v{self.version}'
