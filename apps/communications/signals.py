"""
Django signals for automated email workflows in MAKE CRM
Handles automatic triggering of email workflows based on user actions
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from datetime import timedelta

from apps.contacts.models import Contact
from apps.transactions.models import Transaction
from .services import (
    trigger_automated_workflows,
    send_donation_receipt,
    sync_contact_to_mailchimp,
    WorkflowService,
    ReceiptService
)
from .models import Communication

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Contact)
def handle_new_contact(sender, instance, created, **kwargs):
    """
    Handle new contact creation - trigger welcome series and sync to Mailchimp
    """
    if created:
        try:
            logger.info(f"New contact created: {instance.id} - {instance.full_name}")
            
            # Trigger welcome email series
            trigger_automated_workflows(
                contact=instance,
                event_type='new_contact'
            )
            
            # Sync to Mailchimp if email opt-in is enabled
            if instance.email_opt_in and instance.email:
                sync_contact_to_mailchimp(instance)
                logger.info(f"Contact {instance.id} synced to Mailchimp")
            
        except Exception as e:
            logger.error(f"Failed to handle new contact {instance.id}: {e}")


@receiver(post_save, sender=Contact)
def handle_contact_update(sender, instance, created, **kwargs):
    """
    Handle contact updates - sync changes to Mailchimp if needed
    """
    if not created:
        try:
            # Check if email opt-in status changed
            if hasattr(instance, '_state') and instance._state.adding is False:
                # Get the previous version from database to compare
                try:
                    old_instance = Contact.objects.get(pk=instance.pk)
                    
                    # If email opt-in status changed or email changed, sync to Mailchimp
                    if (old_instance.email_opt_in != instance.email_opt_in or 
                        old_instance.email != instance.email):
                        
                        if instance.email:
                            sync_contact_to_mailchimp(instance)
                            logger.info(f"Contact {instance.id} re-synced to Mailchimp due to changes")
                        
                except Contact.DoesNotExist:
                    pass  # This shouldn't happen, but just in case
                    
        except Exception as e:
            logger.error(f"Failed to handle contact update {instance.id}: {e}")


@receiver(pre_save, sender=Contact)
def store_previous_contact_state(sender, instance, **kwargs):
    """
    Store previous state of contact for comparison in post_save
    """
    if instance.pk:
        try:
            instance._previous_instance = Contact.objects.get(pk=instance.pk)
        except Contact.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def handle_new_donation(sender, instance, created, **kwargs):
    """
    Handle new donation transactions - send receipt and trigger thank you workflow
    """
    if created and instance.type == 'donation' and instance.status == 'completed':
        try:
            logger.info(f"New donation: {instance.id} - ${instance.amount} from {instance.contact.full_name}")
            
            # Send donation receipt automatically
            receipt_sent = send_donation_receipt(instance)
            
            if receipt_sent:
                logger.info(f"Receipt sent for donation {instance.id}")
            else:
                logger.warning(f"Failed to send receipt for donation {instance.id}")
            
            # Trigger donation thank you workflow
            trigger_automated_workflows(
                contact=instance.contact,
                event_type='new_donation',
                transaction=instance
            )
            
            # Update contact's giving totals and RFM score
            instance.contact.update_giving_totals()
            instance.contact.calculate_rfm_score()
            instance.contact.save(update_fields=[
                'total_lifetime_giving', 
                'donation_count', 
                'last_donation_date',
                'rfm_score',
                'donor_segment'
            ])
            
            logger.info(f"Updated RFM score for donor {instance.contact.id}")
            
        except Exception as e:
            logger.error(f"Failed to handle new donation {instance.id}: {e}")


@receiver(post_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, created, **kwargs):
    """
    Handle transaction status changes - send notifications for failed payments, etc.
    """
    if not created and instance.type == 'donation':
        try:
            # Handle failed transactions
            if instance.status == 'failed':
                logger.warning(f"Donation failed: {instance.id} - ${instance.amount} from {instance.contact.full_name}")
                
                # Log failed communication
                Communication.objects.create(
                    contact=instance.contact,
                    type='system',
                    direction='internal',
                    subject=f'Failed donation: ${instance.amount}',
                    content=f'Donation {instance.id} failed - may need follow-up',
                    status='logged',
                    metadata={
                        'transaction_id': str(instance.id),
                        'failure_reason': instance.notes or 'Unknown',
                        'alert_type': 'failed_payment'
                    }
                )
            
            # Handle refunded transactions
            elif instance.status == 'refunded':
                logger.info(f"Donation refunded: {instance.id} - ${instance.amount} from {instance.contact.full_name}")
                
                # Update contact's giving totals
                instance.contact.update_giving_totals()
                instance.contact.calculate_rfm_score()
                instance.contact.save(update_fields=[
                    'total_lifetime_giving', 
                    'donation_count',
                    'rfm_score',
                    'donor_segment'
                ])
                
        except Exception as e:
            logger.error(f"Failed to handle transaction status change {instance.id}: {e}")


def check_lapsed_donors():
    """
    Background task to check for lapsed donors and trigger re-engagement
    This would typically be called by a Celery periodic task
    """
    try:
        # Find contacts who haven't donated in 12+ months but have donated before
        cutoff_date = timezone.now().date() - timedelta(days=365)
        
        lapsed_contacts = Contact.objects.filter(
            donation_count__gt=0,
            last_donation_date__lt=cutoff_date
        ).exclude(
            # Exclude those who have already received lapsed donor emails recently
            communications__metadata__has_key='lapsed_donor_email',
            communications__created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        logger.info(f"Found {lapsed_contacts.count()} lapsed donors to contact")
        
        for contact in lapsed_contacts[:10]:  # Limit to 10 per run to avoid overwhelming
            try:
                trigger_automated_workflows(
                    contact=contact,
                    event_type='lapsed_donor_check'
                )
                logger.info(f"Triggered lapsed donor workflow for {contact.id}")
                
            except Exception as e:
                logger.error(f"Failed to trigger lapsed donor workflow for {contact.id}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to check lapsed donors: {e}")


@receiver(user_logged_in)
def handle_staff_login(sender, request, user, **kwargs):
    """
    Handle staff user login - could trigger reports or notifications
    """
    if user.is_staff:
        logger.info(f"Staff user logged in: {user.username}")
        
        # Could add logic here to:
        # - Send daily/weekly reports
        # - Check for pending tasks
        # - Update dashboard metrics


# Custom signal for major gifts
def handle_major_gift(contact, transaction):
    """
    Custom handler for major gifts (typically $500+)
    """
    try:
        logger.info(f"Major gift received: ${transaction.amount} from {contact.full_name}")
        
        # Send special thank you workflow
        WorkflowService.trigger_donation_thank_you(transaction)
        
        # Create internal notification for staff
        Communication.objects.create(
            contact=contact,
            type='system',
            direction='internal',
            subject=f'Major Gift Alert: ${transaction.amount}',
            content=f'Major gift received from {contact.full_name}. Consider personal follow-up.',
            status='logged',
            metadata={
                'transaction_id': str(transaction.id),
                'alert_type': 'major_gift',
                'amount': str(transaction.amount),
                'donor_segment': contact.donor_segment
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to handle major gift for {contact.id}: {e}")


# Connect the major gift handler to the transaction signal
@receiver(post_save, sender=Transaction)
def check_for_major_gift(sender, instance, created, **kwargs):
    """Check if this is a major gift and handle accordingly"""
    if (created and 
        instance.type == 'donation' and 
        instance.status == 'completed' and 
        instance.amount >= 500):  # $500+ is considered major gift
        
        handle_major_gift(instance.contact, instance)


# Signal for monthly RFM score updates
def update_all_rfm_scores():
    """
    Background task to update RFM scores for all donors
    This would typically be called by a Celery periodic task
    """
    try:
        contacts = Contact.objects.filter(donation_count__gt=0)
        updated_count = 0
        
        for contact in contacts:
            try:
                contact.calculate_rfm_score()
                contact.save(update_fields=['rfm_score', 'donor_segment'])
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update RFM score for contact {contact.id}: {e}")
        
        logger.info(f"Updated RFM scores for {updated_count} contacts")
        
    except Exception as e:
        logger.error(f"Failed to update RFM scores: {e}")


# Export functions for management commands
__all__ = [
    'handle_new_contact',
    'handle_contact_update', 
    'handle_new_donation',
    'handle_transaction_status_change',
    'check_lapsed_donors',
    'update_all_rfm_scores',
    'handle_major_gift'
]