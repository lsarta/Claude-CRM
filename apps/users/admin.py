from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserActivity, Team, TeamMembership


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ['id', 'login_count', 'created_at', 'updated_at']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role', 'get_department']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role', 'profile__department']
    
    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else 'No profile'
    get_role.short_description = 'Role'
    
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') else 'No profile'
    get_department.short_description = 'Department'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'phone', 'can_view_financial_data', 'last_login_ip']
    list_filter = ['role', 'department', 'can_view_all_contacts', 'can_view_financial_data', 'can_manage_events']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['id', 'last_login_ip', 'login_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'department')
        }),
        ('Contact Information', {
            'fields': ('phone', 'mobile', 'emergency_contact')
        }),
        ('Preferences', {
            'fields': ('preferred_contact_method', 'time_zone', 'dashboard_layout', 'notification_preferences'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('can_view_all_contacts', 'can_view_financial_data', 'can_manage_events', 
                      'can_send_communications', 'can_access_reports')
        }),
        ('Activity Tracking', {
            'fields': ('last_login_ip', 'login_count'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'description', 'object_type', 'ip_address', 'created_at']
    list_filter = ['action_type', 'object_type', 'created_at']
    search_fields = ['user__username', 'description', 'object_id']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Activities are created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Activities are immutable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete activity logs


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_lead', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    
    def member_count(self, obj):
        return obj.members.filter(teammembership__is_active=True).count()
    member_count.short_description = 'Active Members'


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'is_active', 'joined_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'team__name']
    readonly_fields = ['joined_date']