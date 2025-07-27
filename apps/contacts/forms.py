from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from .models import Contact, ContactTag, ContactRelationship


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'contact_type', 
            'source', 'address', 'preferences', 'notes', 'primary_contact'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter address as JSON or text'}),
            'preferences': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter preferences as JSON'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('contact_type', css_class='form-group col-md-6 mb-0'),
                Column('source', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'primary_contact',
            'address',
            'preferences',
            'notes',
            Submit('submit', 'Save Contact', css_class='btn btn-primary')
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check for duplicate email (excluding current instance if editing)
            existing = Contact.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('A contact with this email already exists.')
        return email


class ContactSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name or email...',
            'class': 'form-control'
        })
    )
    type = forms.ChoiceField(
        choices=[('', 'All Types')] + Contact.CONTACT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    segment = forms.ChoiceField(
        choices=[('', 'All Segments')] + Contact.DONOR_SEGMENTS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tag = forms.ModelChoiceField(
        queryset=ContactTag.objects.all(),
        required=False,
        empty_label='All Tags',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ContactTagForm(forms.ModelForm):
    class Meta:
        model = ContactTag
        fields = ['name', 'description', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'description',
            'color',
            Submit('submit', 'Save Tag', css_class='btn btn-primary')
        )


class ContactRelationshipForm(forms.ModelForm):
    class Meta:
        model = ContactRelationship
        fields = ['to_contact', 'relationship_type', 'notes']
    
    def __init__(self, *args, **kwargs):
        from_contact = kwargs.pop('from_contact', None)
        super().__init__(*args, **kwargs)
        
        if from_contact:
            # Exclude the from_contact from the to_contact choices
            self.fields['to_contact'].queryset = Contact.objects.exclude(
                pk=from_contact.pk
            )
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'to_contact',
            'relationship_type',
            'notes',
            Submit('submit', 'Add Relationship', css_class='btn btn-primary')
        )


class BulkTagForm(forms.Form):
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    tag = forms.ModelChoiceField(
        queryset=ContactTag.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    action = forms.ChoiceField(
        choices=[('add', 'Add Tag'), ('remove', 'Remove Tag')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ContactImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with contact information',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    has_header = forms.BooleanField(
        label='File has header row',
        initial=True,
        required=False
    )
    update_existing = forms.BooleanField(
        label='Update existing contacts (match by email)',
        initial=False,
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'csv_file',
            'has_header',
            'update_existing',
            HTML('<hr>'),
            HTML('<h5>CSV Format</h5>'),
            HTML('<p>Expected columns: first_name, last_name, email, phone, contact_type, source</p>'),
            Submit('submit', 'Import Contacts', css_class='btn btn-primary')
        )