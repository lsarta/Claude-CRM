from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.contacts.models import Contact
from apps.transactions.models import Transaction, Campaign
from apps.events.models import Event, EventAttendance
from apps.communications.models import EmailCampaign, Communication
from .models import DashboardMetric, ReportTemplate


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current year and month
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # Basic metrics
        context.update({
            'total_contacts': Contact.objects.count(),
            'total_donors': Contact.objects.filter(donation_count__gt=0).count(),
            'total_revenue_ytd': self.get_revenue_ytd(),
            'monthly_revenue': self.get_monthly_revenue(),
            'recent_transactions': Transaction.objects.filter(
                status='completed'
            ).select_related('contact', 'campaign').order_by('-transaction_date')[:10],
            'upcoming_events': Event.objects.filter(
                event_date__gte=now.date(),
                status__in=['promoted', 'registration_open']
            ).order_by('event_date')[:5],
            'donor_segments': self.get_donor_segments(),
            'campaign_performance': self.get_campaign_performance(),
            'recent_communications': Communication.objects.filter(
                created_at__gte=now - timedelta(days=7)
            ).select_related('contact').order_by('-created_at')[:10],
        })
        
        return context
    
    def get_revenue_ytd(self):
        """Get year-to-date revenue"""
        current_year = timezone.now().year
        return Transaction.objects.filter(
            transaction_date__year=current_year,
            status='completed',
            type='donation'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_monthly_revenue(self):
        """Get current month revenue"""
        now = timezone.now()
        return Transaction.objects.filter(
            transaction_date__year=now.year,
            transaction_date__month=now.month,
            status='completed',
            type='donation'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_donor_segments(self):
        """Get donor segment distribution"""
        segments = Contact.objects.filter(
            donor_segment__isnull=False
        ).values('donor_segment').annotate(
            count=Count('id'),
            total_giving=Sum('total_lifetime_giving')
        ).order_by('-total_giving')
        
        return segments
    
    def get_campaign_performance(self):
        """Get recent campaign performance"""
        campaigns = Campaign.objects.filter(
            is_active=True
        ).order_by('-start_date')[:5]
        
        performance = []
        for campaign in campaigns:
            performance.append({
                'name': campaign.name,
                'goal': campaign.goal_amount,
                'raised': campaign.total_raised,
                'progress': campaign.progress_percentage,
                'donors': campaign.donor_count,
            })
        
        return performance


# Placeholder views for other analytics pages
class DonorAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/donor_analytics.html'

class EventAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/event_analytics.html'

class CommunicationAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/communication_analytics.html'

class FinancialAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/financial_analytics.html'

class RFMAnalysisView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/rfm_analysis.html'

class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/report_list.html'

class ReportCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/report_create.html'

class ReportDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/report_detail.html'

class RunReportView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/run_report.html'

# API endpoints for AJAX requests
@login_required
def revenue_trends_api(request):
    """API endpoint for revenue trends chart"""
    # Get last 12 months of revenue data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    # This would typically query monthly aggregated data
    # For now, return sample data
    data = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'datasets': [{
            'label': 'Revenue',
            'data': [15000, 18000, 22000, 19000, 25000, 21000, 
                    23000, 27000, 24000, 28000, 26000, 30000],
            'backgroundColor': 'rgba(54, 162, 235, 0.2)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }]
    }
    
    return JsonResponse(data)

@login_required
def donor_segments_api(request):
    """API endpoint for donor segments pie chart"""
    segments = Contact.objects.filter(
        donor_segment__isnull=False
    ).values('donor_segment').annotate(
        count=Count('id')
    )
    
    data = {
        'labels': [s['donor_segment'].replace('_', ' ').title() for s in segments],
        'datasets': [{
            'data': [s['count'] for s in segments],
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
            ]
        }]
    }
    
    return JsonResponse(data)

@login_required
def event_attendance_api(request):
    """API endpoint for event attendance data"""
    # Sample data - would be calculated from actual events
    data = {
        'labels': ['Literary Readings', 'Workshops', 'Galas', 'Book Launches'],
        'datasets': [{
            'label': 'Average Attendance',
            'data': [45, 25, 120, 35],
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }]
    }
    
    return JsonResponse(data)

@login_required
def campaign_performance_api(request):
    """API endpoint for campaign performance data"""
    campaigns = Campaign.objects.filter(
        is_active=True
    ).order_by('-start_date')[:5]
    
    data = {
        'labels': [c.name for c in campaigns],
        'datasets': [{
            'label': 'Progress %',
            'data': [c.progress_percentage for c in campaigns],
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        }]
    }
    
    return JsonResponse(data)

@login_required
def update_rfm_scores(request):
    """Update RFM scores for all contacts"""
    if request.method == 'POST':
        contacts = Contact.objects.filter(donation_count__gt=0)
        updated_count = 0
        
        for contact in contacts:
            contact.calculate_rfm_score()
            contact.save(update_fields=['rfm_score', 'donor_segment'])
            updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Updated RFM scores for {updated_count} contacts'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def export_dashboard_data(request):
    """Export dashboard data as CSV"""
    # Implementation would create CSV export
    pass

@login_required
def export_report_data(request, pk):
    """Export specific report data"""
    # Implementation would create CSV export for specific report
    pass