import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import Farmer, PerformanceLog, Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'metric_name', 'metric_unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'e.g. Apiculture (Beekeeping)'
            }),
            'metric_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'e.g. Honey Yield'
            }),
            'metric_unit': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'e.g. liters or kg'
            }),
        }

class FarmerForm(forms.ModelForm):
    class Meta:
        model = Farmer
        fields = ['name', 'contact', 'department', 'date_joined', 'location', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'e.g. John Doe'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'Valid phone (e.g. +234-803-123-4567) or email'
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition bg-white'
            }),
            'date_joined': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'Farm address, district, or plot location'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'Farmer background, farm acreage, equipment notes, etc.'
            }),
        }

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()
        if not contact:
            raise ValidationError("Contact information is required.")

        # Check if valid email format
        try:
            validate_email(contact)
            return contact
        except ValidationError:
            pass

        # Check if valid phone format (at least 7 digits, optional +, -, spaces, parentheses)
        digits = re.sub(r'\D', '', contact)
        if len(digits) >= 7 and re.match(r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]*$', contact):
            return contact

        raise ValidationError("Please enter a valid phone number (at least 7 digits) or a valid email address.")


class PerformanceLogForm(forms.ModelForm):
    class Meta:
        model = PerformanceLog
        fields = ['farmer', 'date', 'metric_value', 'notes']
        widgets = {
            'farmer': forms.Select(attrs={
                'id': 'id_farmer_select',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition bg-white'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition'
            }),
            'metric_value': forms.NumberInput(attrs={
                'step': '0.01',
                'inputmode': 'decimal',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition',
                'placeholder': 'Optional observations, weather conditions, mortality notes, etc.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default date to today & prevent future date picking in browser
        today_str = date.today().isoformat()
        if not self.initial.get('date'):
            self.initial['date'] = today_str
        self.fields['date'].widget.attrs['max'] = today_str

        # Only allow logging for ACTIVE farmers
        self.fields['farmer'].queryset = Farmer.objects.filter(status='active').select_related('department')

    def clean_date(self):
        log_date = self.cleaned_data.get('date')
        if log_date and log_date > date.today():
            raise forms.ValidationError("Performance logs cannot be entered for future dates.")
        return log_date
