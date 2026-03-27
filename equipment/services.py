from django.db import transaction
from equipment.repositories import (
    OwnedGearRepository, 
    BrandRepository,
    GuitarRepository,       
    AmplifierRepository,    
    PedalRepository         
)
from equipment.models import OwnedGear


class EquipmentService:
    """
    Service Layer Pattern for Equipment business logic.
    Uses Repository Pattern consistently for all data access.
    """
    
    def __init__(self, user):
        self.user = user
        
        # Repositories for data access
        self.owned_gear_repo = OwnedGearRepository(user=user)
        self.brand_repo = BrandRepository()
        self.guitar_repo = GuitarRepository()
        self.amplifier_repo = AmplifierRepository()
        self.pedal_repo = PedalRepository()
    
    @transaction.atomic
    def add_existing_gear_to_collection(self, gear_type, gear_id, ownership_data):
        """
        Unified method to add ANY gear type from catalog.
        Future-proof: easy to add Drums/Keys later.
        
        Args:
            gear_type: 'guitar', 'amplifier', 'pedal' (must match model field name)
            gear_id: ID from catalog
            ownership_data: dict with nickname, serial, etc.
        """
        
        repos = {
            'guitar': self.guitar_repo,
            'amplifier': self.amplifier_repo,
            'pedal': self.pedal_repo,
        }

        if gear_type not in repos:
            raise ValueError(f"Unsupported gear type: {gear_type}")

        repo = repos[gear_type]
        gear_item = repo.get_by_id(gear_id)

        if not gear_item:
            raise ValueError(f"{gear_type.capitalize()} not found in catalog")

        # e.g. {'guitar': fender obj}
        gear_field_data = {gear_type: gear_item}

        owned_gear = self.owned_gear_repo.create(
            user=self.user,
            **gear_field_data,  # guitar=fender obj
            nickname=ownership_data.get('nickname', ''),
            serial_number=ownership_data.get('serial_number', ''),
            is_favorite=ownership_data.get('is_favorite', False)
        )

        return owned_gear

    @transaction.atomic
    def add_custom_gear(self, gear_type, name, specs, ownership_data):
        """
        Add user's custom gear

        Args
            gear_type: 'guitar', 'amplifier', 'pedal' (must match model field name)
            gear_id: name given by useer
            specs: detailed specs for chosen gear
            ownership_data: dict with nickname, serial, etc.
        """
        unknown_brand = self.brand_repo.get_or_create_unknown()

        repos = {
            'guitar': self.guitar_repo,
            'amplifier': self.amplifier_repo,
            'pedal': self.pedal_repo
        }
        
        if gear_type not in repos:
            raise ValueError(f"Unsupported gear type: {gear_type}")
            
        repo = repos[gear_type]

        custom_item = repo.create_custom(
            brand_obj=unknown_brand, 
            name=name, 
            specs=specs 
        )

        return self.add_existing_gear_to_collection(
            gear_type=gear_type,
            gear_id=custom_item.id,
            ownership_data=ownership_data
        )
    
    def toggle_favorite(self, owned_gear_id):
        owned_gear = self.owned_gear_repo.get_by_id(owned_gear_id)
        
        if not owned_gear:
            raise ValueError("Gear not found")
        
        owned_gear.is_favorite = not owned_gear.is_favorite
        owned_gear.save(update_fields=['is_favorite'])
        
        return owned_gear
    
    def search_and_filter_gear(self, gear_types=None, brand_id=None, search_query=None, favorites_only=False):
        """
        Business logic: Search and filter user's gear.
        Delegates to Repository for actual queries.
        
        Returns:
            QuerySet
        """
        return self.owned_gear_repo.filter_gear(
            gear_types=gear_types if gear_types else None,
            brand_id=brand_id,
            search_query=search_query,
            favorites_only=favorites_only
        )
    
    def get_statistics(self):
        """Get user's gear statistics."""
        return self.owned_gear_repo.count_by_type()
    
