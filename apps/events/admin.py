from django.contrib import admin
from django.utils.html import format_html
from .models import Venue, Event, EventAuthor, EventAttendance, EventSeries, SeriesSubscription


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'formatted_address', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'event_date', 'status', 'registration_count', 'attendance_count']
    list_filter = ['event_type', 'status', 'event_date', 'is_virtual', 'pricing_type']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'registration_count', 'attendance_count', 'waitlist_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'event_type', 'status', 'series')
        }),
        ('Date & Time', {
            'fields': ('event_date', 'start_time', 'end_time', 'registration_deadline')
        }),
        ('Venue & Capacity', {
            'fields': ('venue', 'venue_notes', 'capacity', 'is_virtual', 'virtual_platform', 'virtual_link')
        }),
        ('Pricing', {
            'fields': ('pricing_type', 'base_price', 'member_price', 'student_price')
        }),
        ('Literary Details', {
            'fields': ('literary_genre', 'reading_list'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('event_coordinator', 'volunteers_needed', 'special_requirements'),
            'classes': ('collapse',)
        }),
        ('Marketing', {
            'fields': ('is_public', 'registration_required', 'marketing_budget', 'social_media_hashtag'),
            'classes': ('collapse',)
        }),
        ('Financial Tracking', {
            'fields': ('estimated_expenses', 'actual_expenses', 'estimated_revenue', 'actual_revenue'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('registration_count', 'attendance_count', 'waitlist_count'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventAuthor)
class EventAuthorAdmin(admin.ModelAdmin):
    list_display = ['author', 'event', 'role', 'reading_order', 'honorarium', 'confirmed']
    list_filter = ['role', 'confirmed', 'travel_covered', 'accommodation_covered']
    search_fields = ['author__first_name', 'author__last_name', 'event__name']


@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ['contact', 'event', 'attendance_status', 'registration_date', 'checked_in_at']
    list_filter = ['attendance_status', 'registration_source', 'registration_date']
    search_fields = ['contact__first_name', 'contact__last_name', 'event__name']
    readonly_fields = ['registration_date', 'checked_in_at', 'updated_at']
    
    actions = ['mark_as_attended']
    
    def mark_as_attended(self, request, queryset):
        for attendance in queryset:
            attendance.check_in(request.user)
        self.message_user(request, f"Marked {queryset.count()} attendees as checked in.")
    mark_as_attended.short_description = "Mark selected as attended"


@admin.register(EventSeries)
class EventSeriesAdmin(admin.ModelAdmin):
    list_display = ['name', 'series_type', 'is_recurring', 'event_count', 'total_subscribers', 'is_active']
    list_filter = ['series_type', 'is_recurring', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['event_count', 'total_subscribers', 'created_at', 'updated_at']


@admin.register(SeriesSubscription)
class SeriesSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['contact', 'series', 'subscription_date', 'price_paid', 'is_active', 'auto_register']
    list_filter = ['is_active', 'auto_register', 'subscription_date']
    search_fields = ['contact__first_name', 'contact__last_name', 'series__name']