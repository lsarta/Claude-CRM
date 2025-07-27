from django.contrib import admin
from django.utils.html import format_html
from .models import EmailTemplate, EmailCampaign, Communication, AutomatedWorkflow, UnsubscribeRequest


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'is_default', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_default']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'is_active', 'is_default')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Personalization', {
            'fields': ('merge_fields',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'status', 'total_recipients', 'open_rate_display', 'click_rate_display', 'scheduled_send_time']
    list_filter = ['campaign_type', 'status', 'scheduled_send_time']
    search_fields = ['name', 'subject']
    readonly_fields = ['total_recipients', 'emails_sent', 'emails_delivered', 'emails_opened', 
                      'emails_clicked', 'emails_bounced', 'unsubscribed', 'sent_time', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('name', 'campaign_type', 'template', 'status')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content', 'from_name', 'from_email', 'reply_to_email')
        }),
        ('Scheduling', {
            'fields': ('scheduled_send_time', 'sent_time')
        }),
        ('Targeting', {
            'fields': ('send_to_all_subscribers', 'contact_segments', 'exclude_segments'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('total_recipients', 'emails_sent', 'emails_delivered', 'emails_opened', 
                      'emails_clicked', 'emails_bounced', 'unsubscribed'),
            'classes': ('collapse',)
        }),
        ('Integration', {
            'fields': ('mailchimp_campaign_id', 'external_campaign_id'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def open_rate_display(self, obj):
        rate = obj.open_rate
        color = 'green' if rate >= 25 else 'orange' if rate >= 15 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        rate = obj.click_rate
        color = 'green' if rate >= 5 else 'orange' if rate >= 2 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    click_rate_display.short_description = 'Click Rate'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ['contact', 'type', 'direction', 'subject', 'created_at', 'requires_follow_up']
    list_filter = ['type', 'direction', 'is_private', 'requires_follow_up', 'created_at']
    search_fields = ['contact__first_name', 'contact__last_name', 'subject', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sent_date']
    
    fieldsets = (
        ('Communication Details', {
            'fields': ('contact', 'type', 'direction', 'subject', 'content')
        }),
        ('Context', {
            'fields': ('campaign', 'event', 'transaction', 'parent_communication'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'sent_date')
        }),
        ('Privacy & Permissions', {
            'fields': ('is_private', 'is_confidential')
        }),
        ('Email Tracking', {
            'fields': ('email_message_id', 'email_opened', 'email_clicked', 'email_bounced'),
            'classes': ('collapse',)
        }),
        ('Follow-up', {
            'fields': ('requires_follow_up', 'follow_up_date', 'follow_up_completed')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'author'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(AutomatedWorkflow)
class AutomatedWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'is_active', 'total_triggered', 'total_sent', 'created_at']
    list_filter = ['trigger_type', 'is_active', 'apply_to_all']
    search_fields = ['name', 'description']
    readonly_fields = ['total_triggered', 'total_sent', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UnsubscribeRequest)
class UnsubscribeRequestAdmin(admin.ModelAdmin):
    list_display = ['contact', 'unsubscribe_type', 'email_address', 'processed', 'created_at']
    list_filter = ['unsubscribe_type', 'processed', 'created_at']
    search_fields = ['contact__first_name', 'contact__last_name', 'email_address', 'reason']
    readonly_fields = ['unsubscribe_token', 'created_at', 'processed_date']
    
    actions = ['process_unsubscribes']
    
    def process_unsubscribes(self, request, queryset):
        for unsubscribe in queryset.filter(processed=False):
            unsubscribe.process_unsubscribe(request.user)
        self.message_user(request, f"Processed {queryset.count()} unsubscribe requests.")
    process_unsubscribes.short_description = "Process selected unsubscribe requests"