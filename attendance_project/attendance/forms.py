from django import forms

class AttendanceForm(forms.Form):
    staff_number = forms.CharField(
        max_length=20,
        label="Staff Number",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your staff number',
            'autofocus': True,
            'class': 'form-control'
        })
    )