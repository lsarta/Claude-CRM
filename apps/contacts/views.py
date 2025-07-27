from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from .models import Contact, ContactRelationship, ContactTag, ContactTagAssignment
from .forms import ContactForm, ContactSearchForm, ContactTagForm


class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Contact.objects.all()
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Filter by contact type
        contact_type = self.request.GET.get('type')
        if contact_type:
            queryset = queryset.filter(contact_type=contact_type)
        
        # Filter by donor segment
        segment = self.request.GET.get('segment')
        if segment:
            queryset = queryset.filter(donor_segment=segment)
        
        # Filter by tags
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tag_assignments__tag__id=tag)
        
        return queryset.select_related().order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ContactSearchForm(self.request.GET)
        context['contact_types'] = Contact.CONTACT_TYPES
        context['donor_segments'] = Contact.DONOR_SEGMENTS
        context['tags'] = ContactTag.objects.all()
        return context


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.object
        
        # Get related data
        context['recent_transactions'] = contact.transactions.filter(
            status='completed'
        ).order_by('-transaction_date')[:10]
        
        context['recent_communications'] = contact.communications.order_by(
            '-created_at'
        )[:10]
        
        context['event_attendance'] = contact.event_attendance.select_related(
            'event'
        ).order_by('-event__event_date')[:10]
        
        context['relationships'] = contact.relationships_from.select_related(
            'to_contact'
        ).all()
        
        context['tags'] = contact.tag_assignments.select_related('tag').all()
        
        return context


class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Contact created successfully!')
        return super().form_valid(form)


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Contact updated successfully!')
        return super().form_valid(form)


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Contact deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ContactExportView(LoginRequiredMixin, TemplateView):
    template_name = 'contacts/contact_export.html'


class ContactImportView(LoginRequiredMixin, TemplateView):
    template_name = 'contacts/contact_import.html'


class ContactBulkTagView(LoginRequiredMixin, TemplateView):
    template_name = 'contacts/contact_bulk_tag.html'


class ContactRelationshipView(LoginRequiredMixin, TemplateView):
    template_name = 'contacts/contact_relationships.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = get_object_or_404(Contact, pk=kwargs['pk'])
        context['contact'] = contact
        context['relationships_from'] = contact.relationships_from.select_related('to_contact').all()
        context['relationships_to'] = contact.relationships_to.select_related('from_contact').all()
        return context


class ContactTagListView(LoginRequiredMixin, ListView):
    model = ContactTag
    template_name = 'contacts/tag_list.html'
    context_object_name = 'tags'


class ContactTagCreateView(LoginRequiredMixin, CreateView):
    model = ContactTag
    form_class = ContactTagForm
    template_name = 'contacts/tag_form.html'
    success_url = reverse_lazy('contacts:tag_list')


# AJAX Views
@login_required
def contact_search_ajax(request):
    """AJAX endpoint for contact search autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    contacts = Contact.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    results = []
    for contact in contacts:
        results.append({
            'id': str(contact.id),
            'text': f"{contact.full_name} ({contact.email})",
            'email': contact.email,
            'type': contact.contact_type
        })
    
    return JsonResponse({'results': results})


@login_required
def contact_quick_create_ajax(request):
    """AJAX endpoint for quick contact creation"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.created_by = request.user
            contact.save()
            
            return JsonResponse({
                'success': True,
                'contact': {
                    'id': str(contact.id),
                    'name': contact.full_name,
                    'email': contact.email
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def update_rfm_ajax(request, pk):
    """AJAX endpoint to update RFM score for a contact"""
    if request.method == 'POST':
        contact = get_object_or_404(Contact, pk=pk)
        contact.update_giving_totals()
        contact.calculate_rfm_score()
        contact.save()
        
        return JsonResponse({
            'success': True,
            'rfm_score': contact.rfm_score,
            'donor_segment': contact.get_donor_segment_display() if contact.donor_segment else 'None',
            'total_lifetime_giving': str(contact.total_lifetime_giving),
            'donation_count': contact.donation_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})