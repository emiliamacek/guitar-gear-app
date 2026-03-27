from django.contrib import admin
from .models import Brand, Guitar, Amplifier, Pedal, OwnedGear, GearRequest

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_unknown']
    search_fields = ['name']

# Catalog
@admin.register(Guitar)
class GuitarAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'guitar_type', 'num_strings']
    list_filter = ['guitar_type', 'brand']
    search_fields = ['name', 'brand__name']

@admin.register(Amplifier)
class AmplifierAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'amp_type', 'wattage']
    list_filter = ['amp_type', 'brand']
    search_fields = ['name', 'brand__name']

@admin.register(Pedal)
class PedalAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'pedal_type']
    list_filter = ['pedal_type', 'brand']
    search_fields = ['name', 'brand__name']

# OwnedGear
@admin.register(OwnedGear)
class OwnedGearAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user', 'gear_type_display', 'is_favorite']
    list_filter = ['user', 'is_favorite']
    search_fields = ['nickname', 'guitar__name', 'amplifier__name', 'pedal__name']

    def gear_type_display(self, obj):
        if obj.guitar: return "Guitar"
        if obj.amplifier: return "Amp"
        if obj.pedal: return "Pedal"
        return "-"
    gear_type_display.short_description = "Type"

# Request
@admin.register(GearRequest)
class GearRequestAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'model_name', 'gear_type', 'user', 'status', 'created_at')
    
    list_filter = ('status', 'gear_type', 'created_at')
    
    search_fields = ('brand_name', 'model_name', 'user__username')
    
    readonly_fields = ('created_at',)
    
    ordering = ('-created_at',)

    def get_row_css(self, obj, index):
        if obj.status == 'approved':
            return 'success'
        elif obj.status == 'rejected':
            return 'danger'
        return ''
