import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class EmailTemplate(models.Model):
    """
    Model for managing email templates for automated communications
    """
    TEMPLATE_TYPES = [
        ('donation_thank_you', 'Donation Thank You'),
        ('event_confirmation', 'Event Registration Confirmation'),
        ('event_reminder', 'Event Reminder'),
        ('newsletter', 'Newsletter'),
        ('campaign_launch', 'Campaign Launch'),
        ('lapsed_donor', 'Lapsed Donor Re-engagement'),
        ('welcome', 'Welcome/New Subscriber'),
        ('birthday', 'Birthday Greeting'),
        ('membership_renewal', 'Membership Renewal'),
        ('tax_receipt', 'Tax Receipt'),
        ('pledge_reminder', 'Pledge Reminder'),
        ('volunteer_invitation', 'Volunteer Invitation'),
        ('custom', 'Custom Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    
    # Email content
    subject = models.CharField(max_length=255)
    html_content = models.TextField(help_text="HTML email content with template variables")
    text_content = models.TextField(blank=True, help_text="Plain text fallback")
    
    # Template settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default template for this type")
    
    # Personalization
    merge_fields = models.JSONField(default=list, blank=True, 
                                   help_text="Available merge fields for personalization")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['template_type', 'name']
        unique_together = ['template_type', 'is_default']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render_content(self, context=None):
        """Render template with provided context variables"""
        if not context:
            context = {}
        
        # Simple template rendering - could be enhanced with Django templates
        html_content = self.html_content
        text_content = self.text_content or self.html_content
        subject = self.subject
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'html_content': html_content,
            'text_content': text_content
        }


class EmailCampaign(models.Model):
    """
    Model for managing email marketing campaigns
    """
    CAMPAIGN_TYPES = [
        ('newsletter', 'Newsletter'),
        ('fundraising', 'Fundraising Appeal'),
        ('event_promotion', 'Event Promotion'),
        ('thank_you', 'Thank You Campaign'),
        ('stewardship', 'Stewardship'),
        ('volunteer_recruitment', 'Volunteer Recruitment'),
        ('survey', 'Survey/Feedback'),
        ('announcement', 'Announcement'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    campaign_type = models.CharField(max_length=50, choices=CAMPAIGN_TYPES)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Campaign details
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    from_name = models.CharField(max_length=100, default="MAKE Literary Productions")
    from_email = models.EmailField(default="noreply@makeliterary.org")
    reply_to_email = models.EmailField(blank=True)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_send_time = models.DateTimeField(null=True, blank=True)
    sent_time = models.DateTimeField(null=True, blank=True)
    
    # Segmentation and targeting
    send_to_all_subscribers = models.BooleanField(default=True)
    contact_segments = models.ManyToManyField('contacts.ContactTag', blank=True,
                                            help_text="Send to contacts with these tags")
    exclude_segments = models.ManyToManyField('contacts.ContactTag', blank=True,
                                            related_name='excluded_campaigns',
                                            help_text="Exclude contacts with these tags")
    
    # Analytics (calculated fields)
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_delivered = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    emails_bounced = models.IntegerField(default=0)
    unsubscribed = models.IntegerField(default=0)
    
    # Integration
    mailchimp_campaign_id = models.CharField(max_length=100, blank=True)
    external_campaign_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('communications:campaign_detail', kwargs={'pk': self.pk})
    
    @property
    def open_rate(self):
        """Calculate email open rate as percentage"""
        if self.emails_delivered == 0:
            return 0
        return round((self.emails_opened / self.emails_delivered) * 100, 1)
    
    @property
    def click_rate(self):
        """Calculate click-through rate as percentage"""
        if self.emails_delivered == 0:
            return 0
        return round((self.emails_clicked / self.emails_delivered) * 100, 1)
    
    @property
    def bounce_rate(self):
        """Calculate bounce rate as percentage"""
        if self.emails_sent == 0:
            return 0
        return round((self.emails_bounced / self.emails_sent) * 100, 1)
    
    def get_recipient_list(self):
        """Generate list of contacts for this campaign"""
        from apps.contacts.models import Contact
        
        if self.send_to_all_subscribers:
            contacts = Contact.objects.filter(
                preferences__email_marketing=True,
                email__isnull=False
            ).exclude(email='')
        else:
            # Get contacts with specific tags
            contacts = Contact.objects.filter(
                tag_assignments__tag__in=self.contact_segments.all(),
                preferences__email_marketing=True,
                email__isnull=False
            ).exclude(email='').distinct()
        
        # Exclude contacts with exclusion tags
        if self.exclude_segments.exists():
            contacts = contacts.exclude(
                tag_assignments__tag__in=self.exclude_segments.all()
            )
        
        return contacts
    
    def send_campaign(self):
        """Send the email campaign (placeholder for integration)"""
        # TODO: Integrate with email service provider
        self.status = 'sending'
        self.sent_time = timezone.now()
        self.save()


class Communication(models.Model):
    """
    Model for tracking individual communications with contacts.
    Based on PRD requirements for threaded communication history.
    """
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'In-Person Meeting'),
        ('letter', 'Letter/Mail'),
        ('text', 'Text Message'),
        ('social_media', 'Social Media'),
        ('event_interaction', 'Event Interaction'),
        ('note', 'Internal Note'),
    ]
    
    DIRECTION_CHOICES = [
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound'),
        ('internal', 'Internal Note'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, 
                               related_name='communications')
    
    # Communication details
    type = models.CharField(max_length=50, choices=COMMUNICATION_TYPES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    
    # Context and attribution
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey('transactions.Transaction', on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    
    # Threading for conversations
    parent_communication = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='replies')
    
    # Scheduling and delivery
    scheduled_date = models.DateTimeField(null=True, blank=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    # Privacy and permissions
    is_private = models.BooleanField(default=False, help_text="Private staff note")
    is_confidential = models.BooleanField(default=False, help_text="Highly sensitive information")
    
    # Email-specific fields
    email_message_id = models.CharField(max_length=255, blank=True)
    email_opened = models.BooleanField(default=False)
    email_clicked = models.BooleanField(default=False)
    email_bounced = models.BooleanField(default=False)
    
    # Follow-up tracking
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                              help_text="Staff member who created this communication")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact', '-created_at']),
            models.Index(fields=['type']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['requires_follow_up', 'follow_up_date']),
        ]
    
    def __str__(self):
        return f"{self.contact} - {self.get_type_display()} ({self.created_at.date()})"
    
    def get_absolute_url(self):
        return reverse('communications:detail', kwargs={'pk': self.pk})
    
    @property
    def is_reply(self):
        """Check if this is a reply to another communication"""
        return self.parent_communication is not None
    
    @property
    def reply_count(self):
        """Count of replies to this communication"""
        return self.replies.count()
    
    def mark_as_opened(self):
        """Mark email as opened"""
        if self.type == 'email' and not self.email_opened:
            self.email_opened = True
            self.save(update_fields=['email_opened'])
    
    def mark_as_clicked(self):
        """Mark email as clicked"""
        if self.type == 'email' and not self.email_clicked:
            self.email_clicked = True
            self.save(update_fields=['email_clicked'])


class AutomatedWorkflow(models.Model):
    """
    Model for defining automated communication workflows.
    Based on PRD requirements for automated communication workflows.
    """
    TRIGGER_TYPES = [
        ('transaction_completed', 'Transaction Completed'),
        ('event_registration', 'Event Registration'),
        ('new_contact', 'New Contact Added'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Giving Anniversary'),
        ('lapsed_donor', 'Lapsed Donor'),
        ('pledge_reminder', 'Pledge Reminder'),
        ('membership_expiry', 'Membership Expiring'),
        ('event_reminder', 'Event Reminder'),
        ('follow_up_due', 'Follow-up Due'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    
    # Trigger conditions
    trigger_conditions = models.JSONField(default=dict, blank=True,
                                        help_text="JSON conditions for when to trigger")
    
    # Workflow settings
    is_active = models.BooleanField(default=True)
    delay_days = models.IntegerField(default=0, help_text="Days to wait before sending")
    delay_hours = models.IntegerField(default=0, help_text="Additional hours to wait")
    
    # Target audience
    apply_to_all = models.BooleanField(default=True)
    contact_segments = models.ManyToManyField('contacts.ContactTag', blank=True)
    
    # Email template
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Analytics
    total_triggered = models.IntegerField(default=0)
    total_sent = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
    
    def check_conditions(self, context):
        """Check if workflow conditions are met for given context"""
        if not self.trigger_conditions:
            return True
        
        # Simple condition checking - could be enhanced with complex logic
        for key, expected_value in self.trigger_conditions.items():
            actual_value = context.get(key)
            if actual_value != expected_value:
                return False
        
        return True
    
    def trigger_workflow(self, contact, context=None):
        """Trigger workflow for a specific contact"""
        if not self.is_active:
            return None
        
        if context and not self.check_conditions(context):
            return None
        
        # Check if contact is in target audience
        if not self.apply_to_all and self.contact_segments.exists():
            contact_tags = contact.tag_assignments.values_list('tag', flat=True)
            workflow_tags = self.contact_segments.values_list('id', flat=True)
            if not any(tag in workflow_tags for tag in contact_tags):
                return None
        
        # Calculate send time
        send_time = timezone.now()
        if self.delay_days or self.delay_hours:
            from datetime import timedelta
            delay = timedelta(days=self.delay_days, hours=self.delay_hours)
            send_time += delay
        
        # Create scheduled communication
        communication = Communication.objects.create(
            contact=contact,
            type='email',
            direction='outbound',
            subject=self.email_template.subject if self.email_template else '',
            content=self.email_template.html_content if self.email_template else '',
            scheduled_date=send_time,
            author_id=self.created_by_id
        )
        
        # Update analytics
        self.total_triggered += 1
        self.save(update_fields=['total_triggered'])
        
        return communication


class UnsubscribeRequest(models.Model):
    """
    Model for tracking email unsubscribe requests
    """
    UNSUBSCRIBE_TYPES = [
        ('all_emails', 'All Email Communications'),
        ('marketing', 'Marketing Emails Only'),
        ('newsletters', 'Newsletters Only'),
        ('event_notifications', 'Event Notifications Only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE,
                               related_name='unsubscribe_requests')
    
    # Unsubscribe details
    unsubscribe_type = models.CharField(max_length=50, choices=UNSUBSCRIBE_TYPES)
    email_address = models.EmailField()
    reason = models.TextField(blank=True)
    
    # Source tracking
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    unsubscribe_token = models.CharField(max_length=255, unique=True)
    
    # Processing
    processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contact} - {self.get_unsubscribe_type_display()}"
    
    def process_unsubscribe(self, user=None):
        """Process the unsubscribe request"""
        # Update contact preferences
        preferences = self.contact.preferences or {}
        
        if self.unsubscribe_type == 'all_emails':
            preferences['email_marketing'] = False
            preferences['email_newsletters'] = False
            preferences['email_events'] = False
            preferences['email_transactional'] = False
        elif self.unsubscribe_type == 'marketing':
            preferences['email_marketing'] = False
        elif self.unsubscribe_type == 'newsletters':
            preferences['email_newsletters'] = False
        elif self.unsubscribe_type == 'event_notifications':
            preferences['email_events'] = False
        
        self.contact.preferences = preferences
        self.contact.save()
        
        # Mark as processed
        self.processed = True
        self.processed_date = timezone.now()
        if user:
            self.processed_by = user
        self.save()
    
    def generate_unsubscribe_token(self):
        """Generate unique unsubscribe token"""
        import secrets
        self.unsubscribe_token = secrets.token_urlsafe(32)
        return self.unsubscribe_token