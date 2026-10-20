"""
Models for the stockT stock management application.

Reconstructed to match the production database schema (data/db.sqlite3).
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager supporting custom creation fields."""

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('Users must have a username')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'user')
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Application user with clock number, department and role."""

    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_USER = 'user'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_SUPERVISOR, 'Supervisor'),
        (ROLE_USER, 'User'),
    ]

    clock_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)

    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.is_superuser or self.role == self.ROLE_ADMIN

    @property
    def is_manager(self):
        return self.is_admin or self.role == self.ROLE_MANAGER

    @property
    def is_supervisor(self):
        return self.is_manager or self.role == self.ROLE_SUPERVISOR

    @property
    def role_display(self):
        return self.get_role_display()


class Workspace(models.Model):
    """A workspace is a tenant: each registered user owns one (their "apps"),
    can create more, and can invite other users as members. All stock data
    (kit types, kits, usage) is scoped to a workspace."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_workspaces',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name)[:100] or 'workspace'
            slug = base
            n = 2
            while Workspace.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def owner(self):
        """The user who owns this workspace (first owner membership)."""
        membership = self.memberships.filter(role=WorkspaceMember.ROLE_OWNER).first()
        return membership.user if membership else self.created_by


class WorkspaceMember(models.Model):
    """Membership of a user in a workspace, with a per-workspace role."""

    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Member'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(fields=['workspace', 'user'], name='unique_workspace_user'),
        ]

    def __str__(self):
        return f'{self.user.username} @ {self.workspace.name} ({self.role})'

    @property
    def is_manager(self):
        return self.role in (self.ROLE_OWNER, self.ROLE_ADMIN)


class KitType(models.Model):
    """Type/category of stock kits (e.g. VHB tape, rivnuts, feets)."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    unit_of_measure = models.CharField(max_length=50, default='pieces')
    # Low-stock threshold: when the workspace's total active quantity for
    # this type falls to/below the level, managers are alerted.
    reorder_level = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True,
        related_name='kit_types',
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_kit_types',
    )

    class Meta:
        constraints = [
            # Names/codes are unique per workspace (null workspace = legacy
            # rows, which are exempt so old fixtures keep working).
            models.UniqueConstraint(
                fields=['workspace', 'name'],
                condition=models.Q(workspace__isnull=False),
                name='unique_kit_type_name_per_workspace',
            ),
            models.UniqueConstraint(
                fields=['workspace', 'code'],
                condition=models.Q(workspace__isnull=False),
                name='unique_kit_type_code_per_workspace',
            ),
        ]

    def __str__(self):
        return self.name


class Kit(models.Model):
    """A stock item assigned to a user."""

    CONDITION_NEW = 'new'
    CONDITION_GOOD = 'good'
    CONDITION_FAIR = 'fair'
    CONDITION_POOR = 'poor'
    CONDITION_DAMAGED = 'damaged'
    CONDITION_CHOICES = [
        (CONDITION_NEW, 'New'),
        (CONDITION_GOOD, 'Good'),
        (CONDITION_FAIR, 'Fair'),
        (CONDITION_POOR, 'Poor'),
        (CONDITION_DAMAGED, 'Damaged'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kits')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default=CONDITION_NEW)
    expiration_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True,
        related_name='kits',
    )
    # Legacy field kept for backwards compatibility with older data.
    kit_type_legacy = models.CharField(max_length=20, null=True, blank=True)
    kit_type_string = models.CharField(max_length=20, default='')
    kit_type_fk = models.ForeignKey(
        KitType, on_delete=models.SET_NULL, null=True, blank=True, related_name='kits',
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_kits',
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        name = self.kit_type_fk.name if self.kit_type_fk else self.kit_type_string
        return f'{name} x{self.quantity} ({self.user.username})'

    @property
    def kit_type_name(self):
        return self.kit_type_fk.name if self.kit_type_fk else self.kit_type_string


class UserComment(models.Model):
    """User feedback / bug reports / feature requests."""

    CATEGORY_BUG = 'bug'
    CATEGORY_FEATURE = 'feature'
    CATEGORY_IMPROVEMENT = 'improvement'
    CATEGORY_QUESTION = 'question'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_BUG, 'Bug Report'),
        (CATEGORY_FEATURE, 'Feature Request'),
        (CATEGORY_IMPROVEMENT, 'Improvement'),
        (CATEGORY_QUESTION, 'Question'),
        (CATEGORY_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_REVIEWED = 'reviewed'
    STATUS_RESOLVED = 'resolved'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_REVIEWED, 'Reviewed'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments',
        null=True, blank=True,
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_comments',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.get_status_display()})'


class PasswordResetRequest(models.Model):
    """Password reset requests processed by administrators."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    username = models.CharField(max_length=150)
    clock_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_reset_requests',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_requests')

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f'Reset request for {self.username} ({self.status})'


class ContactInfo(models.Model):
    """Footer contact entries, managed by superadmins."""

    CONTACT_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('address', 'Address'),
        ('website', 'Website'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('other', 'Other'),
    ]

    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_contacts',
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.label}: {self.value}'


class SystemSettings(models.Model):
    """Key/value application settings."""

    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings',
    )

    class Meta:
        verbose_name_plural = 'System settings'

    def __str__(self):
        return f'{self.key}={self.value}'


class StockUsage(models.Model):
    """Records stock usage and triggers automatic stock reduction on approval."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_usages')
    clock_number = models.CharField(max_length=10)
    kit_type_name = models.CharField(max_length=200)
    quantity_used = models.PositiveIntegerField()
    usage_date = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(null=True, blank=True)
    purpose = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    stock_deleted = models.BooleanField(default=False)
    # Soft delete: records are flagged, never destroyed, so the audit trail
    # of who used what (and what stock moved) stays intact.
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deleted_usages',
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True,
        related_name='stock_usages',
    )
    kit = models.ForeignKey(Kit, on_delete=models.SET_NULL, null=True, blank=True, related_name='usages')
    kit_type = models.ForeignKey(
        KitType, on_delete=models.SET_NULL, null=True, blank=True, related_name='usages',
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_usages',
    )

    class Meta:
        ordering = ['-usage_date']
        verbose_name = 'Stock Usage'
        verbose_name_plural = 'Stock Usages'
        permissions = [('review_stock_usage', 'Can review stock usage')]

    def __str__(self):
        return f'{self.user.username} used {self.quantity_used} x {self.kit_type_name}'


class NotificationLog(models.Model):
    """In-app notifications broadcast to selected users."""

    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to = models.ManyToManyField(User, related_name='notifications_received', blank=True)
    read_by = models.ManyToManyField(User, related_name='notifications_read', blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return self.title


class UsageMilestone(models.Model):
    """Usage milestones tracked by the analytics system."""

    milestone_type = models.CharField(max_length=50)
    threshold = models.IntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-achieved_at']

    def __str__(self):
        return f'{self.milestone_type} @ {self.threshold}'


class DeviceTracker(models.Model):
    """Tracks devices used to access the application."""

    device_id = models.CharField(max_length=32, unique=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.CharField(max_length=39, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    total_sessions = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices',
    )

    class Meta:
        ordering = ['-last_seen']

    def __str__(self):
        return f'{self.device_id} ({self.device_type or "unknown"})'


class SessionTracker(models.Model):
    """Tracks user sessions and page navigation."""

    session_id = models.CharField(max_length=32, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.BigIntegerField(null=True, blank=True)
    pages_visited = models.IntegerField(default=0)
    actions_performed = models.IntegerField(default=0)
    last_activity = models.DateTimeField(default=timezone.now)
    entry_page = models.CharField(max_length=500, null=True, blank=True)
    exit_page = models.CharField(max_length=500, null=True, blank=True)
    device = models.ForeignKey(DeviceTracker, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions',
    )
    # Tenant scope captured when the session starts (and filled in on login)
    # so each workspace's analytics only ever include its own members.
    workspace = models.ForeignKey(
        Workspace, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tracked_sessions',
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'Session {self.session_id}'


class PageView(models.Model):
    """Individual page views within a tracked session."""

    page_url = models.CharField(max_length=500)
    page_title = models.CharField(max_length=200, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.IntegerField(default=0)
    session = models.ForeignKey(SessionTracker, on_delete=models.CASCADE, related_name='page_views')

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return self.page_url


class DailyStats(models.Model):
    """Aggregated daily analytics statistics."""

    date = models.DateField(unique=True)
    unique_devices = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    new_devices = models.IntegerField(default=0)
    total_page_views = models.IntegerField(default=0)
    total_actions = models.IntegerField(default=0)
    avg_session_duration = models.BigIntegerField(null=True, blank=True)
    most_visited_page = models.CharField(max_length=500, null=True, blank=True)
    most_visited_page_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Daily stats'

    def __str__(self):
        return f'Stats for {self.date}'
