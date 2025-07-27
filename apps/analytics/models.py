import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class DashboardMetric(models.Model):
    """
    Model for storing calculated dashboard metrics
    """
    METRIC_TYPES = [
        ('total_donors', 'Total Donors'),
        ('total_revenue', 'Total Revenue'),
        ('monthly_revenue', 'Monthly Revenue'),
        ('average_gift_size', 'Average Gift Size'),
        ('donor_retention_rate', 'Donor Retention Rate'),
        ('event_attendance_rate', 'Event Attendance Rate'),
        ('email_open_rate', 'Email Open Rate'),
        ('new_donors_this_month', 'New Donors This Month'),
        ('lapsed_donors', 'Lapsed Donors'),
        ('major_gift_prospects', 'Major Gift Prospects'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        unique_together = ['metric_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}"


class ReportTemplate(models.Model):
    """
    Model for saving custom report configurations
    """
    REPORT_TYPES = [
        ('donor_summary', 'Donor Summary'),
        ('giving_analysis', 'Giving Analysis'),
        ('event_analysis', 'Event Analysis'),
        ('campaign_performance', 'Campaign Performance'),
        ('retention_analysis', 'Retention Analysis'),
        ('board_report', 'Board Report'),
        ('custom', 'Custom Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report configuration
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)
    grouping = models.JSONField(default=dict, blank=True)
    
    # Access control
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_reports')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name