from django import forms
from .models import Amplifier, Guitar, Pedal

class BaseGearForm(forms.ModelForm):
    nickname = forms.CharField(
        required=False,
        label="Nickname",
        help_text="Give your gear a unique name (e.g. 'Old Reliable')",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'My beloved axe'})
    )
    serial_number = forms.CharField(
        required=False, 
        label="Serial Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_favorite = forms.BooleanField(
        required=False, 
        label="Mark as Favorite", 
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class GuitarAddForm(BaseGearForm):
    class Meta:
        model = Guitar
        fields = ["name", "guitar_type", "body_shape", "num_strings", "pickup_config"]
        labels = {
            "name": "Model Name (Custom)",
            "guitar_type": "Type",
            "body_shape": "Body Shape",
            "num_strings": "Number of Strings",
            "pickup_config": "Pickup Configuration (e.g. HSS)",
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'guitar_type': forms.Select(attrs={'class': 'form-select'}),
            'body_shape': forms.Select(attrs={'class': 'form-select'}),
            'num_strings': forms.NumberInput(attrs={'class': 'form-control'}),
            'pickup_config': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AmplifierAddForm(BaseGearForm):
    class Meta:
        model = Amplifier
        fields = ["name", "amp_type", "form_factor", "wattage", "has_effects_loop", "available_controls"]
        labels = {
            "name": "Model Name (Custom)",
            "amp_type": "Technology",
            "form_factor": "Format (Head/Combo)",
            "wattage": "Power (Watts)",
            "has_effects_loop": "Effects Loop?",
            "available_controls": "Knobs/Controls",
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amp_type': forms.Select(attrs={'class': 'form-select'}),
            'form_factor': forms.Select(attrs={'class': 'form-select'}),
            'wattage': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_effects_loop': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'available_controls': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '["Gain", "Volume"]'}),
        }

class PedalAddForm(BaseGearForm):
    class Meta:
        model = Pedal
        fields = ["name", "pedal_type", "bypass_type", "available_controls"]
        labels = {
            "name": "Model Name (Custom)",
            "pedal_type": "Effect Type",
            "bypass_type": "Bypass Type",
            "available_controls": "Knobs/Controls",
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pedal_type': forms.Select(attrs={'class': 'form-select'}),
            'bypass_type': forms.Select(attrs={'class': 'form-select'}),
            'available_controls': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '["Level", "Tone", "Drive"]'}),
        }
