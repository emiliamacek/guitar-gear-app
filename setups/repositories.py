from django.db.models import Q, Prefetch
from django.core.exceptions import ObjectDoesNotExist
from common.repositories import BaseRepository
from setups.models import Setup, SignalChainItem


class SetupRepository(BaseRepository):
    """
    Repository Pattern for Setup (user-scoped).
    Handles all database queries for setups.
    """
    model = Setup
    
    def _get_signal_chain_prefetch(self):
        """
        Private helper: Optimized Prefetch for signal chain.
        Encapsulates optimization logic for related SignalChainItems.
        
        Returns:
            Prefetch object
        """
        return Prefetch(
            'signal_chain',
            queryset=SignalChainItem.objects.select_related(
                'owned_gear',
                'owned_gear__guitar',
                'owned_gear__guitar__brand',
                'owned_gear__amplifier',
                'owned_gear__amplifier__brand',
                'owned_gear__pedal',
                'owned_gear__pedal__brand'
            ).order_by('order')
        )
    
    def get_user_setups(self, include_private=True, optimize_signal_chain=True):
        """
        Get current user's setups with optional optimizations.
        
        Args:
            include_private: If False, only return public setups
            optimize_signal_chain: If True, prefetch signal chain (default)
        
        Returns:
            QuerySet with select_related optimization (Lazy Load pattern)
        """
        queryset = self._get_base_queryset()
        
        if not include_private:
            queryset = queryset.filter(is_public=True)
        
        # Basic optimization
        queryset = queryset.select_related(
            'genre', 
            'band', 
            'song', 
            'song__band'
        )
        
        # Optional: Optimize signal chain (can be disabled if not needed)
        if optimize_signal_chain:
            queryset = queryset.prefetch_related(
                self._get_signal_chain_prefetch()
            )
        
        return queryset.order_by('-is_favorite', '-updated_at')
    
    def get_with_signal_chain(self, setup_id):
        """
        Get single setup with full signal chain optimized.
        Logic: Returns setup if it belongs to user OR is public.
        """
        try:
            # filter user's or public (other) setup
            queryset = self.model.objects.filter(
                Q(user=self.user) | Q(is_public=True),
                id=setup_id
            )

            return queryset.select_related(
                'user', 'genre', 'band', 'song'
            ).prefetch_related(
                self._get_signal_chain_prefetch()
            ).get()
            
        except ObjectDoesNotExist:
            return None
    
    def get_public_setups(self, genre=None, band=None, song=None, gear_query=None, search_query=None, author_username=None, optimize_signal_chain=False):
        """
        Get public setups from ALL users (no user scoping).
        Used for Community page.
        """
        queryset = self.model.objects.filter(is_public=True)
        
        if genre:
            queryset = queryset.filter(genre_id=genre)
        
        if band:
            queryset = queryset.filter(band_id=band)

        if song:
            queryset = queryset.filter(song_id=song)

        if author_username:
            queryset = queryset.filter(user__username=author_username)

        if gear_query:
            queryset = queryset.filter(
                Q(signal_chain__owned_gear__guitar__name__icontains=gear_query) |
                Q(signal_chain__owned_gear__amplifier__name__icontains=gear_query) |
                Q(signal_chain__owned_gear__pedal__name__icontains=gear_query)
            ).distinct()
        # distinct - don't show the same setup multiple times
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(band__name__icontains=search_query) |
                Q(song__title__icontains=search_query)
            )
        
        # Eager Loading
        queryset = queryset.select_related(
            'user', 'genre', 'band', 'song'
        )
        
        if optimize_signal_chain:
            queryset = queryset.prefetch_related(
                self._get_signal_chain_prefetch()
            )
        
        return queryset.order_by('-views', '-created_at')
    
    def get_favorites(self):
        return self._get_base_queryset().filter(
            is_favorite=True
        ).select_related('genre', 'band', 'song')
    
    def increment_views(self, setup_id):
        setup = self.get_by_id(setup_id)
        if setup:
            setup.views += 1
            setup.save(update_fields=['views'])
            return setup
        return None
    
    def toggle_favorite(self, setup_id):
        setup = self.get_by_id(setup_id)
        if setup:
            setup.is_favorite = not setup.is_favorite
            setup.save(update_fields=['is_favorite'])
            return setup
        return None
    
    def toggle_public(self, setup_id):
        setup = self.get_by_id(setup_id)
        if setup:
            setup.is_public = not setup.is_public
            setup.save(update_fields=['is_public'])
            return setup
        return None
    
    def count_by_visibility(self):
        """
        Returns:
            dict: {'public': int, 'private': int}
        """
        base_qs = self._get_base_queryset()
        return {
            'public': base_qs.filter(is_public=True).count(),
            'private': base_qs.filter(is_public=False).count(),
            'favorites': base_qs.filter(is_favorite=True).count(),
        }
    def toggle_save(self, setup_id, user):
        """
        Save/Unsave Setups (Many-to-Many). Works on other public people's setups
        """
        try:
            setup = self.model.objects.filter(
                Q(id=setup_id) & (Q(is_public=True) | Q(user=user))
            ).first()

            if not setup:
                return False

            if user in setup.saved_by.all():
                setup.saved_by.remove(user)
                return False
            else:
                setup.saved_by.add(user)
                return True

        except Exception as e:
            return False
            
    def get_saved_setups(self, user):
        return self.model.objects.filter(saved_by=user).select_related(
            'user', 'genre', 'band', 'song'
        )


class SignalChainRepository(BaseRepository):
    """
    Repository for SignalChainItem.
    Handles signal chain operations.
    """
    model = SignalChainItem
    
    def get_for_setup(self, setup):
        """
        Returns:
            QuerySet ordered by 'order' field
        """
        setup_id = setup.id if hasattr(setup, 'id') else setup
        
        return self.model.objects.filter(
            setup_id=setup_id
        ).select_related(
            'owned_gear',
            'owned_gear__guitar',
            'owned_gear__guitar__brand',
            'owned_gear__amplifier',
            'owned_gear__amplifier__brand',
            'owned_gear__pedal',
            'owned_gear__pedal__brand'
        ).order_by('order')
    
    def add_item(self, setup, owned_gear, order=None, settings=None, notes=''):
        """
            order: Position in chain (auto-calculated if None)
            settings: Dict of settings (Value Object pattern)
            notes: Optional notes
        """
        # Auto-calculate order if not provided
        if order is None:
            max_order = self.model.objects.filter(setup=setup).count()
            order = max_order
        
        return self.model.objects.create(
            setup=setup,
            owned_gear=owned_gear,
            order=order,
            settings=settings or {},
            notes=notes
        )
    
    def remove_item(self, item_id, setup) -> bool:
        try:
            item = self.model.objects.get(id=item_id, setup=setup)
            item.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    # Value Object pattern.
    def update_settings(self, item_id, settings):
        try:
            item = self.model.objects.get(id=item_id)
            item.settings = settings
            item.save(update_fields=['settings'])
            return item
        except ObjectDoesNotExist:
            return None
    
    def reorder(self, setup, new_order):
        for index, item_id in enumerate(new_order):
            self.model.objects.filter(
                id=item_id,
                setup=setup
            ).update(order=index)
    
    def get_count_for_setup(self, setup) -> int:
        setup_id = setup.id if hasattr(setup, 'id') else setup
        return self.model.objects.filter(setup_id=setup_id).count()
