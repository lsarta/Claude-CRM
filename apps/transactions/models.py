import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone


class Campaign(models.Model):
    """
    Model for tracking fundraising campaigns
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Campaign dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Financial goals
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Campaign attributes
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    campaign_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Analytics (calculated fields)
    total_raised = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    donor_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    @property
    def progress_percentage(self):
        """Calculate campaign progress as percentage"""
        if self.goal_amount == 0:
            return 0
        return min(100, round((self.total_raised / self.goal_amount) * 100, 1))
    
    @property
    def is_ongoing(self):
        """Check if campaign is currently active"""
        today = timezone.now().date()
        if not self.end_date:
            return self.start_date <= today and self.is_active
        return self.start_date <= today <= self.end_date and self.is_active
    
    def update_totals(self):
        """Update calculated fields based on transactions"""
        completed_transactions = self.transactions.filter(status='completed')
        self.total_raised = completed_transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.donor_count = completed_transactions.values('contact').distinct().count()
        self.save(update_fields=['total_raised', 'donor_count'])


class Transaction(models.Model):
    """
    Core transaction model for donations, event tickets, and other payments.
    Based on PRD requirements for comprehensive transaction logging.
    """
    TRANSACTION_TYPES = [
        ('donation', 'Donation'),
        ('event_ticket', 'Event Ticket'),
        ('membership', 'Membership'),
        ('merchandise', 'Merchandise'),
        ('book_sales', 'Book Sales'),
        ('workshop_fee', 'Workshop Fee'),
        ('sponsorship', 'Sponsorship'),
        ('grant', 'Grant'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    ]
    
    DONATION_TYPES = [
        ('one_time', 'One-time'),
        ('monthly', 'Monthly Recurring'),
        ('quarterly', 'Quarterly Recurring'),
        ('annual', 'Annual Recurring'),
        ('memorial', 'Memorial Gift'),
        ('honor', 'Honor Gift'),
        ('tribute', 'Tribute Gift'),
        ('matching', 'Matching Gift'),
        ('corporate', 'Corporate Gift'),
        ('foundation', 'Foundation Grant'),
    ]
    
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('venmo', 'Venmo'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('money_order', 'Money Order'),
        ('crypto', 'Cryptocurrency'),
        ('in_kind', 'In-Kind'),
        ('stock', 'Stock Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction basics
    type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Donation-specific fields
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPES, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    
    # Attribution and tracking
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='transactions')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='transactions')
    source_code = models.CharField(max_length=50, blank=True, help_text="Tracking code for campaigns")
    solicitation_method = models.CharField(max_length=50, blank=True, 
                                         help_text="Email, direct mail, phone, event, etc.")
    
    # Payment processing
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    processor_transaction_id = models.CharField(max_length=255, blank=True)
    processor_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Special gift types
    is_memorial = models.BooleanField(default=False)
    memorial_person = models.CharField(max_length=255, blank=True)
    memorial_family_contact = models.ForeignKey('contacts.Contact', on_delete=models.SET_NULL, 
                                               null=True, blank=True, related_name='memorial_gifts')
    
    is_honor_gift = models.BooleanField(default=False)
    honor_person = models.CharField(max_length=255, blank=True)
    honor_contact = models.ForeignKey('contacts.Contact', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='honor_gifts')
    
    # Matching gifts
    is_matching_gift = models.BooleanField(default=False)
    matching_company = models.CharField(max_length=255, blank=True)
    matching_gift_id = models.CharField(max_length=100, blank=True)
    
    # Tax compliance
    is_tax_deductible = models.BooleanField(default=True)
    quid_pro_quo_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                           help_text="Value of goods/services received")
    tax_deductible_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Administrative
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal staff notes, not visible to donor")
    receipt_sent = models.BooleanField(default=False)
    receipt_sent_date = models.DateTimeField(null=True, blank=True)
    thank_you_sent = models.BooleanField(default=False)
    thank_you_sent_date = models.DateTimeField(null=True, blank=True)
    
    # Dates
    transaction_date = models.DateTimeField(default=timezone.now)
    processed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Staff tracking
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='transactions_entered')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transactions_processed')
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['is_recurring']),
            models.Index(fields=['campaign']),
            models.Index(fields=['processor_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.contact} - ${self.amount} ({self.type})"
    
    def get_absolute_url(self):
        return reverse('transactions:detail', kwargs={'pk': self.pk})
    
    @property
    def net_amount(self):
        """Calculate net amount after processor fees"""
        return self.amount - self.processor_fee
    
    @property
    def deductible_amount(self):
        """Calculate tax-deductible amount"""
        if not self.is_tax_deductible:
            return Decimal('0.00')
        
        if self.tax_deductible_amount is not None:
            return self.tax_deductible_amount
        
        # Default calculation: full amount minus quid pro quo value
        return max(Decimal('0.00'), self.amount - self.quid_pro_quo_value)
    
    def save(self, *args, **kwargs):
        """Override save to update contact giving totals and campaign totals"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update contact giving totals if this is a completed donation
        if self.type == 'donation' and self.status == 'completed':
            self.contact.update_giving_totals()
        
        # Update campaign totals
        if self.campaign:
            self.campaign.update_totals()
    
    def process_payment(self, processor_id=None, processor_fee=None):
        """Mark transaction as processed"""
        self.status = 'completed'
        self.processed_date = timezone.now()
        if processor_id:
            self.processor_transaction_id = processor_id
        if processor_fee:
            self.processor_fee = processor_fee
        self.save()
    
    def send_receipt(self):
        """Send tax receipt to donor (placeholder for integration)"""
        # TODO: Implement receipt generation and email sending
        self.receipt_sent = True
        self.receipt_sent_date = timezone.now()
        self.save()
    
    def send_thank_you(self):
        """Send thank you message to donor"""
        # TODO: Implement thank you email system
        self.thank_you_sent = True
        self.thank_you_sent_date = timezone.now()
        self.save()


class RecurringDonation(models.Model):
    """
    Model for managing recurring donation schedules
    """
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Payment Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, 
                               related_name='recurring_donations')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Recurring details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField()
    
    # Payment method
    payment_method = models.CharField(max_length=50, choices=Transaction.PAYMENT_METHODS)
    payment_token = models.CharField(max_length=255, blank=True, help_text="Secure token for payments")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_payments_made = models.IntegerField(default=0)
    total_amount_donated = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_payment_date = models.DateField(null=True, blank=True)
    failed_attempts = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contact} - ${self.amount} {self.frequency}"
    
    def calculate_next_payment_date(self):
        """Calculate the next payment date based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        if self.frequency == 'weekly':
            return self.next_payment_date + relativedelta(weeks=1)
        elif self.frequency == 'monthly':
            return self.next_payment_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            return self.next_payment_date + relativedelta(months=3)
        elif self.frequency == 'semi_annual':
            return self.next_payment_date + relativedelta(months=6)
        elif self.frequency == 'annual':
            return self.next_payment_date + relativedelta(years=1)
        
        return self.next_payment_date
    
    def process_recurring_payment(self):
        """Process a recurring payment and create transaction record"""
        # Create transaction record
        transaction = Transaction.objects.create(
            contact=self.contact,
            type='donation',
            donation_type=f'{self.frequency}_recurring',
            amount=self.amount,
            is_recurring=True,
            campaign=self.campaign,
            payment_method=self.payment_method,
            is_tax_deductible=True,
            transaction_date=timezone.now()
        )
        
        # Update recurring donation record
        self.total_payments_made += 1
        self.total_amount_donated += self.amount
        self.last_payment_date = timezone.now().date()
        self.next_payment_date = self.calculate_next_payment_date()
        self.save()
        
        return transaction


class Pledge(models.Model):
    """
    Model for tracking pledges and multi-payment commitments
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='pledges')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pledge details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_schedule = models.CharField(max_length=50, blank=True)
    
    # Dates
    pledge_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    fulfillment_date = models.DateField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reminder_sent_count = models.IntegerField(default=0)
    last_reminder_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-pledge_date']
    
    def __str__(self):
        return f"{self.contact} - ${self.total_amount} pledge"
    
    @property
    def amount_remaining(self):
        """Calculate remaining amount to be paid"""
        return self.total_amount - self.amount_paid
    
    @property
    def is_fulfilled(self):
        """Check if pledge is fully paid"""
        return self.amount_paid >= self.total_amount
    
    @property
    def is_overdue(self):
        """Check if pledge is overdue"""
        if not self.due_date:
            return False
        return timezone.now().date() > self.due_date and not self.is_fulfilled
    
    def update_from_transactions(self):
        """Update amount paid based on related transactions"""
        related_transactions = Transaction.objects.filter(
            contact=self.contact,
            campaign=self.campaign,
            status='completed',
            transaction_date__gte=self.pledge_date
        )
        
        self.amount_paid = related_transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        if self.is_fulfilled and self.status == 'active':
            self.status = 'fulfilled'
            self.fulfillment_date = timezone.now().date()
        elif self.is_overdue and self.status == 'active':
            self.status = 'overdue'
        
        self.save()


class TaxReceipt(models.Model):
    """
    Model for tracking tax receipt generation and delivery
    """
    RECEIPT_TYPES = [
        ('single', 'Single Transaction'),
        ('annual', 'Annual Summary'),
        ('quarterly', 'Quarterly Summary'),
    ]
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('sent', 'Sent'),
        ('bounced', 'Email Bounced'),
        ('printed', 'Printed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='tax_receipts')
    receipt_type = models.CharField(max_length=20, choices=RECEIPT_TYPES)
    
    # Receipt details
    receipt_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deductible_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Date range for summary receipts
    start_date = models.DateField()
    end_date = models.DateField()
    
    # File management
    pdf_file = models.FileField(upload_to='tax_receipts/', blank=True)
    
    # Delivery tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    email_sent_date = models.DateTimeField(null=True, blank=True)
    email_address = models.EmailField(blank=True)
    
    # Related transactions
    transactions = models.ManyToManyField(Transaction, related_name='tax_receipts')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.contact}"
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        year = self.start_date.year
        # Get the next sequential number for this year
        last_receipt = TaxReceipt.objects.filter(
            receipt_number__startswith=f"{year}-"
        ).order_by('-receipt_number').first()
        
        if last_receipt:
            last_num = int(last_receipt.receipt_number.split('-')[1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        self.receipt_number = f"{year}-{next_num:06d}"
        return self.receipt_number