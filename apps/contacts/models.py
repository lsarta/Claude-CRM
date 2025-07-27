import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json


class Contact(models.Model):
    """
    Core contact model representing donors, prospects, volunteers, and board members.
    Based on PRD requirements for unified contact profiles.
    """
    CONTACT_TYPES = [
        ('prospect', 'Prospect'),
        ('donor', 'Donor'),
        ('volunteer', 'Volunteer'),
        ('board_member', 'Board Member'),
        ('staff', 'Staff'),
        ('vendor', 'Vendor'),
        ('author', 'Author/Speaker'),
    ]
    
    DONOR_SEGMENTS = [
        ('champions', 'Champions'),
        ('loyal_customers', 'Loyal Customers'),
        ('new_customers', 'New Customers'),
        ('at_risk', 'At Risk'),
        ('needs_attention', 'Needs Attention'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address stored as JSON for flexibility
    address = models.JSONField(default=dict, blank=True)
    
    # Contact classification
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPES, default='prospect')
    source = models.CharField(max_length=100, blank=True, help_text="How did they hear about us?")
    
    # Preferences and notes
    preferences = models.JSONField(default=dict, blank=True, help_text="Communication preferences, interests, etc.")
    notes = models.TextField(blank=True)
    
    # Calculated donor analytics fields
    total_lifetime_giving = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_donation_date = models.DateField(null=True, blank=True)
    donation_count = models.IntegerField(default=0)
    rfm_score = models.CharField(max_length=3, blank=True, help_text="RFM analysis score")
    donor_segment = models.CharField(max_length=50, choices=DONOR_SEGMENTS, blank=True)
    
    # Relationship tracking
    primary_contact = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      help_text="Primary contact for organizations or spouses")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contacts_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contacts_updated')
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['donor_segment']),
            models.Index(fields=['last_donation_date']),
            models.Index(fields=['total_lifetime_giving']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('contacts:detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
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
    
    def calculate_rfm_score(self):
        """
        Calculate RFM (Recency, Frequency, Monetary) score for donor segmentation.
        Based on PRD requirements for automated donor segmentation.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Recency score (1-5, 5 being most recent)
        if self.last_donation_date:
            days_since_last = (timezone.now().date() - self.last_donation_date).days
            if days_since_last <= 90:
                recency = 5
            elif days_since_last <= 180:
                recency = 4
            elif days_since_last <= 365:
                recency = 3
            elif days_since_last <= 730:
                recency = 2
            else:
                recency = 1
        else:
            recency = 1
        
        # Frequency score (1-5, 5 being most frequent)
        if self.donation_count >= 10:
            frequency = 5
        elif self.donation_count >= 5:
            frequency = 4
        elif self.donation_count >= 3:
            frequency = 3
        elif self.donation_count >= 1:
            frequency = 2
        else:
            frequency = 1
        
        # Monetary score (1-5, 5 being highest value)
        if self.total_lifetime_giving >= 1000:
            monetary = 5
        elif self.total_lifetime_giving >= 500:
            monetary = 4
        elif self.total_lifetime_giving >= 100:
            monetary = 3
        elif self.total_lifetime_giving >= 25:
            monetary = 2
        else:
            monetary = 1
        
        self.rfm_score = f"{recency}{frequency}{monetary}"
        
        # Determine donor segment based on RFM
        if recency >= 4 and frequency >= 4 and monetary >= 4:
            self.donor_segment = 'champions'
        elif recency >= 4 and frequency >= 3 and monetary >= 3:
            self.donor_segment = 'loyal_customers'
        elif recency >= 4 and frequency <= 2:
            self.donor_segment = 'new_customers'
        elif recency <= 2 and frequency >= 3 and monetary >= 3:
            self.donor_segment = 'at_risk'
        else:
            self.donor_segment = 'needs_attention'
        
        return self.rfm_score
    
    def update_giving_totals(self):
        """Update calculated giving fields based on transactions"""
        from apps.transactions.models import Transaction
        
        donations = Transaction.objects.filter(
            contact=self,
            type='donation',
            status='completed'
        )
        
        self.total_lifetime_giving = donations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.donation_count = donations.count()
        
        latest_donation = donations.order_by('-transaction_date').first()
        if latest_donation:
            self.last_donation_date = latest_donation.transaction_date.date()
        
        # Recalculate RFM score
        self.calculate_rfm_score()


class ContactRelationship(models.Model):
    """
    Model for tracking relationships between contacts (spouse, family, organizational connections)
    Based on PRD requirement for relationship mapping
    """
    RELATIONSHIP_TYPES = [
        ('spouse', 'Spouse'),
        ('partner', 'Partner'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('colleague', 'Colleague'),
        ('board_connection', 'Board Connection'),
        ('organization', 'Organization'),
        ('referral', 'Referral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='relationships_from')
    to_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='relationships_to')
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_TYPES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['from_contact', 'to_contact', 'relationship_type']
    
    def __str__(self):
        return f"{self.from_contact} -> {self.to_contact} ({self.relationship_type})"


class ContactTag(models.Model):
    """
    Flexible tagging system for contacts
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ContactTagAssignment(models.Model):
    """
    Many-to-many through table for contact tags
    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='tag_assignments')
    tag = models.ForeignKey(ContactTag, on_delete=models.CASCADE, related_name='contact_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['contact', 'tag']
    
    def __str__(self):
        return f"{self.contact} - {self.tag}"