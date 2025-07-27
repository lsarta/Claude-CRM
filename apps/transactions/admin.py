from django.contrib import admin
from django.utils.html import format_html
from .models import Campaign, Transaction, RecurringDonation, Pledge, TaxReceipt


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'goal_amount', 'total_raised', 'progress_display', 'is_active']
    list_filter = ['is_active', 'is_public', 'start_date']
    search_fields = ['name', 'description']
    readonly_fields = ['total_raised', 'donor_count', 'created_at', 'updated_at']
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        color = 'green' if percentage >= 100 else 'orange' if percentage >= 75 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            percentage
        )
    progress_display.short_description = 'Progress'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['contact', 'type', 'amount', 'status', 'payment_method', 'transaction_date', 'campaign']
    list_filter = ['type', 'status', 'payment_method', 'is_recurring', 'is_tax_deductible', 'transaction_date']
    search_fields = ['contact__first_name', 'contact__last_name', 'processor_transaction_id']
    readonly_fields = ['id', 'net_amount', 'deductible_amount', 'created_at', 'updated_at', 'processed_date']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('contact', 'type', 'amount', 'quantity', 'status')
        }),
        ('Donation Details', {
            'fields': ('donation_type', 'is_recurring', 'recurring_frequency', 'next_payment_date'),
            'classes': ('collapse',)
        }),
        ('Attribution', {
            'fields': ('campaign', 'event', 'source_code', 'solicitation_method')
        }),
        ('Payment Processing', {
            'fields': ('payment_method', 'processor_transaction_id', 'processor_fee', 'net_amount')
        }),
        ('Special Gift Types', {
            'fields': ('is_memorial', 'memorial_person', 'memorial_family_contact', 
                      'is_honor_gift', 'honor_person', 'honor_contact',
                      'is_matching_gift', 'matching_company', 'matching_gift_id'),
            'classes': ('collapse',)
        }),
        ('Tax Compliance', {
            'fields': ('is_tax_deductible', 'quid_pro_quo_value', 'tax_deductible_amount', 'deductible_amount')
        }),
        ('Administration', {
            'fields': ('notes', 'internal_notes', 'receipt_sent', 'receipt_sent_date', 
                      'thank_you_sent', 'thank_you_sent_date'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('transaction_date', 'processed_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Staff Tracking', {
            'fields': ('entered_by', 'processed_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'send_receipts']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='completed')
        self.message_user(request, f"Marked {updated} transactions as completed.")
    mark_as_completed.short_description = "Mark selected as completed"
    
    def send_receipts(self, request, queryset):
        for transaction in queryset.filter(status='completed', receipt_sent=False):
            transaction.send_receipt()
        self.message_user(request, f"Sent receipts for {queryset.count()} transactions.")
    send_receipts.short_description = "Send receipts for selected transactions"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.entered_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecurringDonation)
class RecurringDonationAdmin(admin.ModelAdmin):
    list_display = ['contact', 'amount', 'frequency', 'status', 'next_payment_date', 'total_payments_made']
    list_filter = ['frequency', 'status', 'start_date']
    search_fields = ['contact__first_name', 'contact__last_name']
    readonly_fields = ['total_payments_made', 'total_amount_donated', 'last_payment_date', 'created_at', 'updated_at']


@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = ['contact', 'total_amount', 'amount_paid', 'amount_remaining', 'status', 'due_date']
    list_filter = ['status', 'pledge_date', 'due_date']
    search_fields = ['contact__first_name', 'contact__last_name']
    readonly_fields = ['amount_remaining', 'created_at', 'updated_at']
    
    def amount_remaining(self, obj):
        remaining = obj.amount_remaining
        color = 'green' if remaining == 0 else 'orange' if remaining < obj.total_amount * 0.5 else 'red'
        return format_html(
            '<span style="color: {};">${:,.2f}</span>',
            color,
            remaining
        )
    amount_remaining.short_description = 'Remaining'


@admin.register(TaxReceipt)
class TaxReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'contact', 'receipt_type', 'total_amount', 'status', 'email_sent_date']
    list_filter = ['receipt_type', 'status', 'start_date']
    search_fields = ['receipt_number', 'contact__first_name', 'contact__last_name']
    readonly_fields = ['receipt_number', 'created_at']
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.receipt_number:
            obj.generate_receipt_number()
        if not change:
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)