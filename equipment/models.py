from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_unknown = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    @classmethod
    def get_unknown_brand(cls):
        brand, _ = cls.objects.get_or_create(
            name="Unknown", defaults={"is_unknown": True}
        )
        return brand


class Gear(models.Model):
    """Abstract Base Class for Catalog items"""
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="%(class)s_set"
    )
    
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class Guitar(Gear):
    GUITAR_TYPE_CHOICES = [
        ("ELECTRIC", "Electric Guitar"),
        ("ELECTRO_ACOUSTIC", "Electro-Acoustic Guitar"), 
        ("BASS", "Bass Guitar"),
        ("OTHER", "Other"),
    ]
    
    BODY_SHAPE_CHOICES = [
        # Electric
        ("STRAT", "Stratocaster Style"),
        ("TELE", "Telecaster Style"),
        ("LP", "Les Paul Style"),
        ("SG", "SG Style"),
        ("OFFSET", "Offset (Jazzmaster/Jaguar)"),
        ("SUPERSTRAT", "Superstrat"),
        ("HOLLOW", "Hollow Body / Semi-Hollow"),
        
        # Acoustic
        ("DREADNOUGHT", "Dreadnought"),
        ("CUTAWAY", "Acoustic with Cutaway"),
        ("PARLOR", "Parlor / Folk"),
        ("CLASSICAL_SHAPE", "Classical Shape"),
        
        ("OTHER", "Other"),
    ]

    guitar_type = models.CharField(choices=GUITAR_TYPE_CHOICES, max_length=20)
    body_shape = models.CharField(choices=BODY_SHAPE_CHOICES, max_length=20, default="OTHER")
    num_strings = models.IntegerField(default=6)
    
    # e.g. "HSS", "Piezo + Mic", "Piezo only"
    pickup_config = models.CharField(max_length=50, blank=True)


class Amplifier(Gear):
    AMP_TECH_CHOICES = [
        ("TUBE", "Tube (Valve)"),
        ("SOLID_STATE", "Solid State"),
        ("DIGITAL", "Digital/Modeling"),
        ("HYBRID", "Hybrid"),
    ]
    
    AMP_FORM_CHOICES = [
        ("HEAD", "Head"),
        ("COMBO", "Combo"),
        ("RACK", "Rackmount"),
        ("PEDAL", "Pedal Amp"),
    ]

    amp_type = models.CharField(choices=AMP_TECH_CHOICES, max_length=20)
    form_factor = models.CharField(choices=AMP_FORM_CHOICES, max_length=20, default="HEAD")
    wattage = models.IntegerField(help_text="Power in watts")
    num_channels = models.IntegerField(default=1)
    has_effects_loop = models.BooleanField(default=False)

    # e.g. ["Gain", "Bass", "Middle", "Treble", "Master"]
    available_controls = models.JSONField(default=list, blank=True)


class Pedal(Gear):
    PEDAL_TYPE_CHOICES = [
        ("OVERDRIVE", "Overdrive"),
        ("DISTORTION", "Distortion"),
        ("FUZZ", "Fuzz"),
        ("BOOST", "Boost"),
        ("DELAY", "Delay"),
        ("REVERB", "Reverb"),
        ("MODULATION", "Modulation (Chorus/Phaser/Flanger)"),
        ("COMPRESSOR", "Compressor"),
        ("TUNER", "Tuner"),
        ("MULTI", "Multi-Effects"),
        ("OTHER", "Other"),
    ]
    
    BYPASS_CHOICES = [
        ("TRUE", "True Bypass"),
        ("BUFFERED", "Buffered"),
        ("UNKNOWN", "Unknown"),
    ]

    pedal_type = models.CharField(choices=PEDAL_TYPE_CHOICES, max_length=20)
    bypass_type = models.CharField(choices=BYPASS_CHOICES, max_length=20, default="UNKNOWN")

    # e.g. ["Level", "Tone", "Drive"]
    available_controls = models.JSONField(default=list, blank=True)


class OwnedGear(models.Model):
    """
    User's specific instance of gear.
    Links a User to a Catalog Item (Guitar/Amp/Pedal).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_gear"
    )

    # Only one can be filled
    guitar = models.ForeignKey(Guitar, on_delete=models.PROTECT, null=True, blank=True)
    amplifier = models.ForeignKey(Amplifier, on_delete=models.PROTECT, null=True, blank=True)
    pedal = models.ForeignKey(Pedal, on_delete=models.PROTECT, null=True, blank=True)

    # User's settings
    nickname = models.CharField(max_length=100, blank=True, help_text="e.g. 'My Old Strat'")
    serial_number = models.CharField(max_length=100, blank=True)
    is_favorite = models.BooleanField(default=False)
    
    acquired_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Modifications, history, etc.")

    # e.g. {"Gain": 5, "Bass": 7, "Treble": 4}
    user_settings = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_favorite", "-created_at"]
        indexes = [
            models.Index(fields=['user', 'is_favorite']),
        ]

    def clean(self):
        """Ensure only one type of gear is associated per entry"""
        gear_count = sum([
            1 if self.guitar else 0,
            1 if self.amplifier else 0,
            1 if self.pedal else 0
        ])
        
        if gear_count == 0:
            raise ValidationError("OwnedGear must be associated with a Guitar, Amplifier, or Pedal.")
        if gear_count > 1:
            raise ValidationError("OwnedGear can only be one type of gear (Guitar OR Amplifier OR Pedal).")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def gear_item(self):
        """Returns the actual gear object from the catalog"""
        return self.guitar or self.amplifier or self.pedal
        
    @property
    def type_name(self):
        """Returns string representation of type for templates"""
        if self.guitar: return "Guitar"
        if self.amplifier: return "Amplifier"
        if self.pedal: return "Pedal"
        return "Unknown"

    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.gear_item})"
        return str(self.gear_item)

class GearRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    gear_type = models.CharField(max_length=20, choices=[
        ('guitar', 'Guitar'), ('amplifier', 'Amplifier'), ('pedal', 'Pedal')
    ])
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand_name} {self.model_name} ({self.status})"
