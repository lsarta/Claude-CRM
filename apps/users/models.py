import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


class UserProfile(models.Model):
    """
    Extended user profile for CRM staff members.
    Based on PRD requirements for role-based access control.
    """
    USER_ROLES = [
        ('system_admin', 'System Administrator'),
        ('executive_director', 'Executive Director'),
        ('individual_giving_manager', 'Individual Giving Manager'),
        ('grants_director', 'Grants Director'),
        ('board_member', 'Board Member'),
        ('social_media_manager', 'Social Media Manager'),
        ('volunteer_coordinator', 'Volunteer Coordinator'),
        ('event_coordinator', 'Event Coordinator'),
        ('development_assistant', 'Development Assistant'),
        ('intern', 'Intern'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Role and permissions
    role = models.CharField(max_length=50, choices=USER_ROLES)
    department = models.CharField(max_length=100, blank=True)
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    
    # Work preferences
    preferred_contact_method = models.CharField(max_length=20, default='email',
                                              choices=[('email', 'Email'), ('phone', 'Phone'), ('slack', 'Slack')])
    time_zone = models.CharField(max_length=50, default='America/Chicago')
    
    # System preferences
    dashboard_layout = models.JSONField(default=dict, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # Access control
    can_view_all_contacts = models.BooleanField(default=False)
    can_view_financial_data = models.BooleanField(default=False)
    can_manage_events = models.BooleanField(default=False)
    can_send_communications = models.BooleanField(default=False)
    can_access_reports = models.BooleanField(default=True)
    
    # Activity tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    def get_permissions(self):
        """
        Get user permissions based on role.
        Based on PRD permission matrix.
        """
        role_permissions = {
            'system_admin': {
                'view_all_donors': True,
                'view_financial_data': True,
                'manage_board_contacts': True,
                'access_strategic_reports': True,
                'manage_campaigns': True,
                'manage_users': True,
                'system_settings': True,
            },
            'executive_director': {
                'view_all_donors': True,
                'view_financial_data': True,
                'manage_board_contacts': True,
                'access_strategic_reports': True,
                'manage_campaigns': True,
                'manage_users': False,
                'system_settings': False,
            },
            'individual_giving_manager': {
                'manage_individual_donors': True,
                'view_prospect_research': True,
                'create_cultivation_plans': True,
                'manage_acknowledgments': True,
                'limited_financial_data': True,
                'no_board_personal_info': True,
                'no_staff_salary_data': True,
            },
            'grants_director': {
                'view_program_data': True,
                'manage_foundation_contacts': True,
                'access_outcome_reports': True,
                'coordinate_applications': True,
            },
            'board_member': {
                'view_dashboard_metrics': True,
                'access_assigned_prospects': True,
                'view_campaign_progress': True,
                'no_detailed_donor_info': True,
                'no_staff_internal_data': True,
            },
            'social_media_manager': {
                'view_engagement_preferences': True,
                'access_story_content': True,
                'manage_social_campaigns': True,
                'no_financial_data': True,
                'opt_in_required_for_features': True,
            },
        }
        
        return role_permissions.get(self.role, {})
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = self.get_permissions()
        return permissions.get(permission, False)


class UserActivity(models.Model):
    """
    Model for tracking user activity for security and analytics
    """
    ACTION_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('view_contact', 'Viewed Contact'),
        ('edit_contact', 'Edited Contact'),
        ('create_transaction', 'Created Transaction'),
        ('send_email', 'Sent Email'),
        ('run_report', 'Ran Report'),
        ('export_data', 'Exported Data'),
        ('delete_record', 'Deleted Record'),
        ('admin_action', 'Admin Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    
    # Activity details
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.CharField(max_length=255)
    
    # Context
    object_type = models.CharField(max_length=50, blank=True, help_text="Model name")
    object_id = models.CharField(max_length=50, blank=True, help_text="Object ID")
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()}"


class Team(models.Model):
    """
    Model for organizing users into teams
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Team lead
    team_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='teams_led')
    
    # Members
    members = models.ManyToManyField(User, through='TeamMembership', related_name='teams')
    
    # Settings
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    """
    Through model for team memberships with additional details
    """
    MEMBERSHIP_ROLES = [
        ('member', 'Member'),
        ('lead', 'Team Lead'),
        ('coordinator', 'Coordinator'),
        ('specialist', 'Specialist'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=MEMBERSHIP_ROLES, default='member')
    
    # Dates
    joined_date = models.DateField(auto_now_add=True)
    left_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'team']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team.name} ({self.role})"