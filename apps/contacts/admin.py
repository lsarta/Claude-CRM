from django.contrib import admin
from django.utils.html import format_html
from .models import Contact, ContactRelationship, ContactTag, ContactTagAssignment


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'contact_type', 'donor_segment', 'total_lifetime_giving', 'last_donation_date']
    list_filter = ['contact_type', 'donor_segment', 'source', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['id', 'total_lifetime_giving', 'donation_count', 'last_donation_date', 'rfm_score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Classification', {
            'fields': ('contact_type', 'source', 'primary_contact')
        }),
        ('Address', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('Donor Analytics', {
            'fields': ('total_lifetime_giving', 'donation_count', 'last_donation_date', 'rfm_score', 'donor_segment'),
            'classes': ('collapse',)
        }),
        ('Preferences & Notes', {
            'fields': ('preferences', 'notes'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContactRelationship)
class ContactRelationshipAdmin(admin.ModelAdmin):
    list_display = ['from_contact', 'relationship_type', 'to_contact', 'created_at']
    list_filter = ['relationship_type', 'created_at']
    search_fields = ['from_contact__first_name', 'from_contact__last_name', 'to_contact__first_name', 'to_contact__last_name']


@admin.register(ContactTag)
class ContactTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_display', 'created_at']
    search_fields = ['name', 'description']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.name
        )
    color_display.short_description = 'Color'


@admin.register(ContactTagAssignment)
class ContactTagAssignmentAdmin(admin.ModelAdmin):
    list_display = ['contact', 'tag', 'assigned_by', 'assigned_at']
    list_filter = ['tag', 'assigned_at']
    search_fields = ['contact__first_name', 'contact__last_name', 'tag__name']