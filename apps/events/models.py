import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta


class Venue(models.Model):
    """
    Venue model for storing venue information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.JSONField(default=dict, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    contact_info = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def formatted_address(self):
        """Return formatted address string from JSON data"""
        if not self.address:
            return ""
        
        parts = []
        if self.address.get('street'):
            parts.append(self.address['street'])
        if self.address.get('city'):
            parts.append(self.address['city'])
        if self.address.get('state'):
            parts.append(self.address['state'])
        if self.address.get('zip_code'):
            parts.append(self.address['zip_code'])
        
        return ", ".join(parts)


class Event(models.Model):
    """
    Core event model for literary programming and fundraising events.
    Based on PRD requirements for multi-format event types.
    """
    EVENT_TYPES = [
        ('reading', 'Literary Reading'),
        ('workshop', 'Workshop'),
        ('gala', 'Gala/Fundraiser'),
        ('book_launch', 'Book Launch'),
        ('literary_series', 'Literary Series'),
        ('panel', 'Panel Discussion'),
        ('conference', 'Conference'),
        ('networking', 'Networking Event'),
        ('volunteer', 'Volunteer Event'),
        ('board_meeting', 'Board Meeting'),
        ('online', 'Online Event'),
        ('hybrid', 'Hybrid Event'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('promoted', 'Being Promoted'),
        ('registration_open', 'Registration Open'),
        ('sold_out', 'Sold Out'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    
    PRICING_TYPES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
        ('suggested_donation', 'Suggested Donation'),
        ('member_discount', 'Member Pricing'),
        ('tiered', 'Tiered Pricing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Date and time
    event_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Venue and capacity
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)
    venue_notes = models.TextField(blank=True, help_text="Special venue arrangements, setup notes")
    capacity = models.IntegerField(null=True, blank=True)
    is_virtual = models.BooleanField(default=False)
    virtual_platform = models.CharField(max_length=100, blank=True, help_text="Zoom, YouTube, etc.")
    virtual_link = models.URLField(blank=True)
    
    # Pricing and ticketing
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPES, default='free')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    member_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    student_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Literary-specific fields
    featured_authors = models.ManyToManyField('contacts.Contact', through='EventAuthor', 
                                            related_name='featured_events', blank=True)
    literary_genre = models.CharField(max_length=100, blank=True, 
                                    help_text="Poetry, Fiction, Non-fiction, etc.")
    reading_list = models.TextField(blank=True, help_text="Books or works to be discussed/read")
    
    # Organization and logistics
    event_coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='coordinated_events')
    volunteers_needed = models.IntegerField(default=0)
    special_requirements = models.TextField(blank=True, 
                                          help_text="AV needs, catering, accessibility, etc.")
    
    # Marketing and promotion
    is_public = models.BooleanField(default=True)
    registration_required = models.BooleanField(default=False)
    marketing_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    social_media_hashtag = models.CharField(max_length=100, blank=True)
    
    # Financial tracking
    estimated_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    estimated_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Analytics (calculated fields)
    registration_count = models.IntegerField(default=0)
    attendance_count = models.IntegerField(default=0)
    waitlist_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events_created')
    
    class Meta:
        ordering = ['-event_date', 'start_time']
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.event_date}"
    
    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'pk': self.pk})
    
    @property
    def is_past(self):
        """Check if event date has passed"""
        from django.utils import timezone
        return self.event_date < timezone.now().date()
    
    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return not self.is_past
    
    @property
    def is_sold_out(self):
        """Check if event is at capacity"""
        if not self.capacity:
            return False
        return self.registration_count >= self.capacity
    
    @property
    def available_spots(self):
        """Calculate remaining capacity"""
        if not self.capacity:
            return None
        return max(0, self.capacity - self.registration_count)
    
    @property
    def attendance_rate(self):
        """Calculate attendance rate as percentage"""
        if self.registration_count == 0:
            return 0
        return round((self.attendance_count / self.registration_count) * 100, 1)
    
    @property
    def net_revenue(self):
        """Calculate net revenue (revenue - expenses)"""
        return self.actual_revenue - self.actual_expenses
    
    @property
    def roi_percentage(self):
        """Calculate ROI as percentage"""
        if self.actual_expenses == 0:
            return 0
        return round(((self.actual_revenue - self.actual_expenses) / self.actual_expenses) * 100, 1)
    
    def update_registration_count(self):
        """Update registration count based on EventAttendance records"""
        self.registration_count = self.attendance_records.filter(
            attendance_status__in=['registered', 'attended', 'no_show']
        ).count()
        self.save(update_fields=['registration_count'])
    
    def update_attendance_count(self):
        """Update attendance count based on check-ins"""
        self.attendance_count = self.attendance_records.filter(
            attendance_status='attended'
        ).count()
        self.save(update_fields=['attendance_count'])


class EventAuthor(models.Model):
    """
    Through model for Event-Author relationships with additional details
    """
    ROLE_CHOICES = [
        ('featured', 'Featured Author'),
        ('moderator', 'Moderator'),
        ('panelist', 'Panelist'),
        ('keynote', 'Keynote Speaker'),
        ('interviewer', 'Interviewer'),
        ('special_guest', 'Special Guest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='author_relationships')
    author = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='event_relationships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='featured')
    reading_order = models.IntegerField(null=True, blank=True, help_text="Order for readings/presentations")
    honorarium = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    travel_covered = models.BooleanField(default=False)
    accommodation_covered = models.BooleanField(default=False)
    bio_text = models.TextField(blank=True, help_text="Bio for this specific event")
    special_requests = models.TextField(blank=True)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'author']
        ordering = ['reading_order', 'author__last_name']
    
    def __str__(self):
        return f"{self.author} - {self.event.name} ({self.role})"


class EventAttendance(models.Model):
    """
    Tracks registration and attendance for events.
    Based on PRD requirements for attendance tracking and integration.
    """
    ATTENDANCE_STATUS = [
        ('registered', 'Registered'),
        ('waitlisted', 'Waitlisted'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]
    
    REGISTRATION_SOURCE = [
        ('website', 'Website'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('in_person', 'In Person'),
        ('social_media', 'Social Media'),
        ('referral', 'Referral'),
        ('member_portal', 'Member Portal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='event_attendance')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='registered')
    registration_source = models.CharField(max_length=20, choices=REGISTRATION_SOURCE, default='website')
    
    # Registration details
    registration_date = models.DateTimeField(auto_now_add=True)
    ticket_price_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Attendance tracking
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='checked_in_attendees')
    
    # Preferences and special needs
    dietary_restrictions = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    
    # Post-event feedback
    feedback_rating = models.IntegerField(null=True, blank=True, 
                                        help_text="1-5 rating")
    feedback_comments = models.TextField(blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)
    
    # Communication preferences
    email_reminders = models.BooleanField(default=True)
    sms_reminders = models.BooleanField(default=False)
    
    # Notes and admin fields
    admin_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['contact', 'event']
        ordering = ['registration_date']
        indexes = [
            models.Index(fields=['attendance_status']),
            models.Index(fields=['registration_date']),
            models.Index(fields=['checked_in_at']),
        ]
    
    def __str__(self):
        return f"{self.contact} - {self.event.name} ({self.attendance_status})"
    
    def check_in(self, user=None):
        """Mark attendee as checked in"""
        from django.utils import timezone
        self.attendance_status = 'attended'
        self.checked_in_at = timezone.now()
        if user:
            self.checked_in_by = user
        self.save()
        
        # Update event attendance count
        self.event.update_attendance_count()
    
    def send_reminder(self):
        """Send event reminder (placeholder for email integration)"""
        # TODO: Implement email reminder system
        pass


class EventSeries(models.Model):
    """
    Model for managing recurring event series (reading series, workshops, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    series_type = models.CharField(max_length=50, choices=Event.EVENT_TYPES)
    
    # Recurring patterns
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, 
                                        help_text="weekly, monthly, quarterly")
    season_start = models.DateField(null=True, blank=True)
    season_end = models.DateField(null=True, blank=True)
    
    # Subscription and membership
    subscription_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    member_discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Series coordinator
    coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Marketing
    series_image = models.ImageField(upload_to='event_series/', blank=True)
    social_media_handle = models.CharField(max_length=100, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Event Series'
    
    def __str__(self):
        return self.name
    
    @property
    def event_count(self):
        """Count of events in this series"""
        return self.events.count()
    
    @property
    def total_subscribers(self):
        """Count of series subscribers"""
        return self.subscriptions.filter(is_active=True).count()


class SeriesSubscription(models.Model):
    """
    Track subscriptions to event series
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey(EventSeries, on_delete=models.CASCADE, related_name='subscriptions')
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='series_subscriptions')
    subscription_date = models.DateTimeField(auto_now_add=True)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    auto_register = models.BooleanField(default=True, help_text="Automatically register for new events")
    
    class Meta:
        unique_together = ['series', 'contact']
    
    def __str__(self):
        return f"{self.contact} - {self.series.name}"


# Add the series relationship to Event
Event.add_to_class('series', models.ForeignKey(EventSeries, on_delete=models.SET_NULL, 
                                              null=True, blank=True, related_name='events'))