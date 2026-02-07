from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Profile, Message, Rating


class UserRegistrationForm(UserCreationForm):
    """Enhanced registration form with profile fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True)
    phone = forms.CharField(max_length=20, required=False)
    location = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    """Form to update user profile"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Profile
        fields = ['role', 'phone', 'location', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


class ProductForm(forms.ModelForm):
    """Form to create and edit products"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'condition', 'image', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name != 'is_available':
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            else:
                self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})


class MessageForm(forms.ModelForm):
    """Form to send messages"""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Type your message here...'
            }),
        }


class RatingForm(forms.ModelForm):
    """Form to rate sellers"""
    class Meta:
        model = Rating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Share your experience with this seller (optional)...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['review'].required = False
