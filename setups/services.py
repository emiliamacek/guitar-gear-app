from django.db import transaction
from django.core.exceptions import ValidationError

from setups.repositories import SetupRepository, SignalChainRepository
from equipment.repositories import OwnedGearRepository
from setups.models import Setup


class SetupService:
    """
    Service Layer Pattern for Setup business logic.
    Coordinates operations between repositories and enforces business rules.
    """
    
    def __init__(self, user):
        self.user = user
        self.setup_repo = SetupRepository(user=user)
        self.signal_chain_repo = SignalChainRepository()
        self.owned_gear_repo = OwnedGearRepository(user=user)
    
    @transaction.atomic  # Unit of Work pattern
    def create_setup(self, name, description='', genre=None, band=None, song=None, is_public=False):
        """
        Auto-tagging is handled by Setup.save() (Domain Model pattern).
        """
        # Validation
        if not name or not name.strip():
            raise ValueError("Setup name is required")
        
        # Create setup using repository
        setup_data = {
            'name': name.strip(),
            'description': description.strip() if description else '',
            'genre': genre,
            'band': band,
            'song': song,
            'is_public': is_public
        }
        
        setup = self.setup_repo.create(**setup_data)
        
        # Note: Auto-tagging (song → band → genre) happens in Setup.save(
        # This is Domain Model pattern
        
        return setup
    
    @transaction.atomic  # Unit of Work pattern
    def add_gear_to_setup(self, setup_id, owned_gear_id, order=None, settings=None, notes=''):
        """
        Add gear to setup's signal chain.
        Business logic: validates ownership, prevents duplicates.
        
        Args:
            order: Position in chain (auto-calculated if None)
            settings: Dict of knob settings (Value Object pattern)
            notes: Optional notes
        """

        setup = self.setup_repo.get_by_id(setup_id)
        if not setup:
            raise ValueError("Setup not found or doesn't belong to you")
        
        owned_gear = self.owned_gear_repo.get_by_id(owned_gear_id)
        if not owned_gear:
            raise ValueError("Gear not found or doesn't belong to you")
        
        existing = self.signal_chain_repo.model.objects.filter(
            setup=setup,
            owned_gear=owned_gear
        ).exists()
        
        if existing:
            raise ValueError(f"{owned_gear} is already in this setup")
        
        # 4. Add to signal chain (order auto-calculated in repository if None)
        item = self.signal_chain_repo.add_item(
            setup=setup,
            owned_gear=owned_gear,
            order=order,
            settings=settings or {},
            notes=notes
        )
        
        return item
    
    @transaction.atomic
    def remove_gear_from_setup(self, setup_id, item_id):
        setup = self.setup_repo.get_by_id(setup_id)
        if not setup:
            raise ValueError("Setup not found")
        
        success = self.signal_chain_repo.remove_item(item_id, setup)
        
        if not success:
            raise ValueError("Item not found in signal chain")
        
        return success
    
    
    @transaction.atomic
    def toggle_save_setup(self, setup_id):
        is_saved = self.setup_repo.toggle_save(setup_id, self.user)
        return is_saved

    def get_saved_setups(self):
        return self.setup_repo.get_saved_setups(self.user)
    def update_gear_settings(self, setup_id, item_id, settings):
        setup = self.setup_repo.get_by_id(setup_id)
        if not setup:
            raise ValueError("Setup not found")
        
        item = self.signal_chain_repo.update_settings(item_id, settings)
        
        if not item:
            raise ValueError("Signal chain item not found")
        
        if item.setup_id != setup.id:
            raise ValueError("Item doesn't belong to this setup")
        
        return item
    
    def reorder_signal_chain(self, setup_id, item_ids_in_order):
        setup = self.setup_repo.get_by_id(setup_id)
        if not setup:
            raise ValueError("Setup not found")
        
        # Validate all items belong to this setup
        existing_items = set(
            self.signal_chain_repo.get_for_setup(setup).values_list('id', flat=True)
        )
        provided_items = set(item_ids_in_order)
        
        if existing_items != provided_items:
            raise ValueError("Item list doesn't match setup's signal chain")
        
        self.signal_chain_repo.reorder(setup, item_ids_in_order)
    
    def toggle_favorite(self, setup_id):
        setup = self.setup_repo.toggle_favorite(setup_id)
        
        if not setup:
            raise ValueError("Setup not found")
        
        return setup
    
    def publish_setup(self, setup_id):
        """
        Business rule: Only owner can publish.
        """
        setup = self.setup_repo.get_by_id(setup_id)
        
        if not setup:
            raise ValueError("Setup not found")
        
        if not setup.is_public:
            setup = self.setup_repo.toggle_public(setup_id)
        
        return setup
    
    def unpublish_setup(self, setup_id):
        setup = self.setup_repo.get_by_id(setup_id)
        
        if not setup:
            raise ValueError("Setup not found")
        
        if setup.is_public:
            setup = self.setup_repo.toggle_public(setup_id)
        
        return setup
    
    def get_user_setups(self, include_private=True):
        return self.setup_repo.get_user_setups(include_private=include_private)
    
    def get_setup_with_chain(self, setup_id):
        return self.setup_repo.get_with_signal_chain(setup_id)
    

    def get_public_setups(self, genre=None, band=None, song=None, gear_query=None, search_query=None, author_username=None):
        public_repo = SetupRepository()
        return public_repo.get_public_setups(
            genre=genre, band=band, song=song, 
            gear_query=gear_query, search_query=search_query,
            author_username=author_username # <--- Przekazujemy
        )
    
    def increment_views(self, setup_id):
        # Use repo without user for public setups
        public_repo = SetupRepository()
        public_repo.increment_views(setup_id)
    
    def get_statistics(self):
        """
        Returns:
            dict with stats
        """
        stats = self.setup_repo.count_by_visibility()
        
        # Add signal chain stats
        all_setups = self.setup_repo.get_user_setups()
        total_gear_items = sum(
            self.signal_chain_repo.get_count_for_setup(setup)
            for setup in all_setups
        )
        
        stats['total_setups'] = all_setups.count()
        stats['total_gear_in_chains'] = total_gear_items
        
        return stats
