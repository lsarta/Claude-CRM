"""
Email service integrations for MAKE CRM
Handles Mailchimp API integration, automated receipt generation, and email workflows
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

from .models import EmailCampaign, Communication, AutomatedWorkflow
from apps.contacts.models import Contact
from apps.transactions.models import Transaction

logger = logging.getLogger(__name__)


class MailchimpService:
    """Mailchimp API integration service"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAILCHIMP_API_KEY', None)
        self.server = getattr(settings, 'MAILCHIMP_SERVER', 'us1')
        self.base_url = f'https://{self.server}.api.mailchimp.com/3.0'
        self.headers = {
            'Authorization': f'apikey {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Mailchimp"""
        if not self.api_key:
            logger.error("Mailchimp API key not configured")
            return {'error': 'API key not configured'}
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Mailchimp API error: {e}")
            return {'error': str(e)}
    
    def sync_contact(self, contact: Contact, list_id: str) -> Dict:
        """Sync a contact to Mailchimp list"""
        data = {
            'email_address': contact.email,
            'status': 'subscribed' if contact.email_opt_in else 'unsubscribed',
            'merge_fields': {
                'FNAME': contact.first_name,
                'LNAME': contact.last_name,
                'PHONE': contact.phone or '',
            },
            'tags': [tag.tag.name for tag in contact.tag_assignments.all()],
            'interests': {},
            'vip': contact.donor_segment in ['champions', 'loyal_customers']
        }
        
        # Add custom merge fields
        if contact.contact_type:
            data['merge_fields']['CTYPE'] = contact.contact_type
        
        if contact.donor_segment:
            data['merge_fields']['DSEGMENT'] = contact.donor_segment
        
        # Use subscriber hash for updates
        subscriber_hash = contact.email.lower()
        
        return self._make_request(
            'PUT', 
            f'lists/{list_id}/members/{subscriber_hash}',
            data
        )
    
    def create_campaign(self, campaign_data: Dict) -> Dict:
        """Create a new email campaign in Mailchimp"""
        return self._make_request('POST', 'campaigns', campaign_data)
    
    def send_campaign(self, campaign_id: str) -> Dict:
        """Send a campaign"""
        return self._make_request('POST', f'campaigns/{campaign_id}/actions/send')
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get campaign statistics"""
        return self._make_request('GET', f'campaigns/{campaign_id}')
    
    def create_segment(self, list_id: str, segment_data: Dict) -> Dict:
        """Create audience segment based on donor data"""
        return self._make_request('POST', f'lists/{list_id}/segments', segment_data)
    
    def bulk_sync_contacts(self, contacts: List[Contact], list_id: str) -> Dict:
        """Bulk sync multiple contacts"""
        operations = []
        
        for contact in contacts:
            operations.append({
                'method': 'PUT',
                'path': f'/lists/{list_id}/members/{contact.email.lower()}',
                'body': json.dumps({
                    'email_address': contact.email,
                    'status': 'subscribed' if contact.email_opt_in else 'unsubscribed',
                    'merge_fields': {
                        'FNAME': contact.first_name,
                        'LNAME': contact.last_name,
                        'PHONE': contact.phone or '',
                        'CTYPE': contact.contact_type or '',
                        'DSEGMENT': contact.donor_segment or '',
                    }
                })
            })
        
        batch_data = {'operations': operations}
        return self._make_request('POST', 'batches', batch_data)


class ReceiptService:
    """Automated receipt generation service"""
    
    @staticmethod
    def generate_donation_receipt(transaction: Transaction) -> bytes:
        """Generate PDF receipt for donation transaction"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Organization header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "MAKE Literary Productions")
        p.setFont("Helvetica", 12)
        p.drawString(100, 730, "Chicago Literary Arts Organization")
        p.drawString(100, 715, "Tax ID: XX-XXXXXXX")  # Replace with actual EIN
        
        # Receipt title
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 680, "DONATION RECEIPT")
        
        # Receipt details
        p.setFont("Helvetica", 12)
        y_position = 650
        
        receipt_data = [
            ("Receipt Number:", str(transaction.id)[:8]),
            ("Date:", transaction.transaction_date.strftime("%B %d, %Y")),
            ("Donor:", transaction.contact.full_name),
            ("Address:", getattr(transaction.contact, 'formatted_address', 'N/A')),
            ("Email:", transaction.contact.email),
            ("", ""),
            ("Donation Amount:", f"${transaction.amount:,.2f}"),
            ("Payment Method:", transaction.get_payment_method_display()),
            ("Campaign:", transaction.campaign.name if transaction.campaign else "General Fund"),
        ]
        
        for label, value in receipt_data:
            if label:
                p.drawString(100, y_position, f"{label}")
                p.drawString(250, y_position, str(value))
            y_position -= 20
        
        # Tax deductibility notice
        y_position -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y_position, "Tax Deductibility Notice:")
        p.setFont("Helvetica", 10)
        y_position -= 15
        
        tax_notice = [
            "This donation is tax-deductible to the full extent allowed by law.",
            "No goods or services were provided in exchange for this contribution.",
            "Please retain this receipt for your tax records.",
            "Thank you for supporting literary arts in Chicago!"
        ]
        
        for line in tax_notice:
            p.drawString(100, y_position, line)
            y_position -= 15
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(100, 50, f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def send_receipt_email(transaction: Transaction):
        """Send receipt via email"""
        try:
            # Generate PDF receipt
            pdf_data = ReceiptService.generate_donation_receipt(transaction)
            
            # Create email
            subject = f"Donation Receipt - MAKE Literary Productions"
            
            # Email content
            context = {
                'transaction': transaction,
                'contact': transaction.contact,
                'organization_name': 'MAKE Literary Productions'
            }
            
            html_content = render_to_string('communications/receipt_email.html', context)
            text_content = render_to_string('communications/receipt_email.txt', context)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[transaction.contact.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Attach PDF receipt
            email.attach(
                f"receipt_{transaction.id}.pdf",
                pdf_data,
                'application/pdf'
            )
            
            email.send()
            
            # Log communication
            Communication.objects.create(
                contact=transaction.contact,
                type='email',
                direction='outbound',
                subject=subject,
                content=f"Automated donation receipt sent for ${transaction.amount}",
                status='sent',
                metadata={
                    'transaction_id': str(transaction.id),
                    'receipt_generated': True,
                    'email_type': 'receipt'
                }
            )
            
            logger.info(f"Receipt sent for transaction {transaction.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send receipt for transaction {transaction.id}: {e}")
            
            # Log failed communication
            Communication.objects.create(
                contact=transaction.contact,
                type='email',
                direction='outbound',
                subject=subject,
                content=f"Failed to send receipt: {str(e)}",
                status='failed',
                metadata={
                    'transaction_id': str(transaction.id),
                    'error': str(e),
                    'email_type': 'receipt'
                }
            )
            return False


class WorkflowService:
    """Automated email workflow service"""
    
    @staticmethod
    def trigger_welcome_series(contact: Contact):
        """Trigger welcome email series for new contacts"""
        try:
            workflow = AutomatedWorkflow.objects.get(
                name='new_contact_welcome',
                is_active=True
            )
            
            # Send immediate welcome email
            WorkflowService._send_workflow_email(
                contact=contact,
                template='welcome_immediate',
                subject='Welcome to MAKE Literary Productions!',
                delay_minutes=0
            )
            
            # Schedule follow-up emails
            WorkflowService._schedule_workflow_email(
                contact=contact,
                template='literary_events_intro',
                subject='Discover Our Literary Events',
                delay_days=3
            )
            
            WorkflowService._schedule_workflow_email(
                contact=contact,
                template='ways_to_support',
                subject='Ways to Support Chicago\'s Literary Scene',
                delay_days=7
            )
            
            logger.info(f"Welcome series triggered for contact {contact.id}")
            
        except AutomatedWorkflow.DoesNotExist:
            logger.warning("Welcome workflow not configured")
        except Exception as e:
            logger.error(f"Failed to trigger welcome series: {e}")
    
    @staticmethod
    def trigger_donation_thank_you(transaction: Transaction):
        """Trigger donation thank you workflow"""
        try:
            # Send immediate thank you
            WorkflowService._send_workflow_email(
                contact=transaction.contact,
                template='donation_thank_you',
                subject='Thank You for Your Support!',
                delay_minutes=0,
                context={'transaction': transaction}
            )
            
            # Schedule impact update if major donor
            if transaction.amount >= Decimal('250.00'):
                WorkflowService._schedule_workflow_email(
                    contact=transaction.contact,
                    template='impact_update_major',
                    subject='The Impact of Your Generous Support',
                    delay_days=30,
                    context={'transaction': transaction}
                )
            
            logger.info(f"Thank you workflow triggered for transaction {transaction.id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger donation thank you: {e}")
    
    @staticmethod
    def trigger_lapsed_donor_reengagement(contact: Contact):
        """Trigger re-engagement series for lapsed donors"""
        try:
            # Check if contact hasn't donated in 12+ months
            last_donation = contact.transactions.filter(
                type='donation',
                status='completed'
            ).order_by('-transaction_date').first()
            
            if not last_donation:
                return
            
            months_since_last = (timezone.now().date() - last_donation.transaction_date).days / 30
            
            if months_since_last >= 12:
                WorkflowService._send_workflow_email(
                    contact=contact,
                    template='lapsed_donor_reengagement',
                    subject='We Miss Your Support',
                    delay_minutes=0,
                    context={'last_donation': last_donation}
                )
                
                logger.info(f"Lapsed donor reengagement sent to {contact.id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger lapsed donor workflow: {e}")
    
    @staticmethod
    def _send_workflow_email(contact: Contact, template: str, subject: str, 
                           delay_minutes: int = 0, context: Dict = None):
        """Send workflow email immediately or with delay"""
        try:
            email_context = {
                'contact': contact,
                'organization_name': 'MAKE Literary Productions',
                **(context or {})
            }
            
            html_content = render_to_string(f'communications/workflows/{template}.html', email_context)
            text_content = render_to_string(f'communications/workflows/{template}.txt', email_context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contact.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Log communication
            Communication.objects.create(
                contact=contact,
                type='email',
                direction='outbound',
                subject=subject,
                content=f"Automated workflow email: {template}",
                status='sent',
                metadata={
                    'workflow_template': template,
                    'email_type': 'workflow'
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to send workflow email {template}: {e}")
    
    @staticmethod
    def _schedule_workflow_email(contact: Contact, template: str, subject: str, 
                               delay_days: int, context: Dict = None):
        """Schedule workflow email for future delivery (would use Celery in production)"""
        # In production, this would use Celery delayed tasks
        # For now, we'll log the scheduling
        logger.info(f"Scheduled workflow email '{template}' for contact {contact.id} in {delay_days} days")


class EmailCampaignService:
    """Email campaign management service"""
    
    @staticmethod
    def create_segment_campaign(segment: str, campaign_data: Dict) -> EmailCampaign:
        """Create targeted campaign for specific donor segment"""
        try:
            # Get contacts in segment
            contacts = Contact.objects.filter(donor_segment=segment)
            
            campaign = EmailCampaign.objects.create(
                name=campaign_data['name'],
                subject=campaign_data['subject'],
                content=campaign_data['content'],
                template=campaign_data.get('template', 'default'),
                target_segment=segment,
                created_by_id=campaign_data['created_by_id'],
                metadata={
                    'target_count': contacts.count(),
                    'segment': segment
                }
            )
            
            # Add recipients
            campaign.recipients.set(contacts)
            
            logger.info(f"Created segment campaign {campaign.id} for {segment}")
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to create segment campaign: {e}")
            raise
    
    @staticmethod
    def send_campaign(campaign: EmailCampaign) -> Dict:
        """Send email campaign to all recipients"""
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            for contact in campaign.recipients.all():
                try:
                    # Personalized content
                    context = {
                        'contact': contact,
                        'campaign': campaign,
                        'organization_name': 'MAKE Literary Productions'
                    }
                    
                    html_content = render_to_string(
                        f'communications/campaigns/{campaign.template}.html', 
                        context
                    )
                    text_content = render_to_string(
                        f'communications/campaigns/{campaign.template}.txt', 
                        context
                    )
                    
                    email = EmailMultiAlternatives(
                        subject=campaign.subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[contact.email]
                    )
                    
                    email.attach_alternative(html_content, "text/html")
                    email.send()
                    
                    # Log communication
                    Communication.objects.create(
                        contact=contact,
                        type='email',
                        direction='outbound',
                        subject=campaign.subject,
                        content=f"Campaign: {campaign.name}",
                        status='sent',
                        email_campaign=campaign,
                        metadata={
                            'campaign_id': str(campaign.id),
                            'email_type': 'campaign'
                        }
                    )
                    
                    results['sent'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {contact.email}: {str(e)}")
                    logger.error(f"Failed to send campaign email to {contact.email}: {e}")
            
            # Update campaign status
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.metadata.update({
                'results': results,
                'completion_time': timezone.now().isoformat()
            })
            campaign.save()
            
            logger.info(f"Campaign {campaign.id} sent: {results['sent']} success, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to send campaign {campaign.id}: {e}")
            campaign.status = 'failed'
            campaign.save()
            raise


# Integration helper functions
def sync_contact_to_mailchimp(contact: Contact):
    """Helper function to sync single contact to Mailchimp"""
    mailchimp = MailchimpService()
    list_id = getattr(settings, 'MAILCHIMP_MAIN_LIST_ID', None)
    
    if list_id:
        return mailchimp.sync_contact(contact, list_id)
    else:
        logger.warning("Mailchimp main list ID not configured")
        return {'error': 'List ID not configured'}

def send_donation_receipt(transaction: Transaction):
    """Helper function to send donation receipt"""
    return ReceiptService.send_receipt_email(transaction)

def trigger_automated_workflows(contact: Contact, event_type: str, **kwargs):
    """Helper function to trigger appropriate workflows based on events"""
    if event_type == 'new_contact':
        WorkflowService.trigger_welcome_series(contact)
    elif event_type == 'new_donation':
        transaction = kwargs.get('transaction')
        if transaction:
            WorkflowService.trigger_donation_thank_you(transaction)
    elif event_type == 'lapsed_donor_check':
        WorkflowService.trigger_lapsed_donor_reengagement(contact)