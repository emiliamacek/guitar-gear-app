from django.db.models import Q, QuerySet
from common.repositories import BaseRepository
from equipment.models import OwnedGear, Brand, Guitar, Amplifier, Pedal

"""
Repository DO NOT throw exceptions. If something hasn't been found -> None is returned.
Exceptions are raised by Services!

Single Repositories for every gear
"""

"""
QuerySet:
We aren't fetching data every time
instead, we're building a query that will only be evaluated when the data
is actually accessed (e.g., in a loop, list, or template).
"""

class BrandRepository(BaseRepository):
    """
    Repository for Brand model (global, no user scoping).
    """
    model = Brand
    
    def search(self, query):
        """Search brands by name"""
        return self.model.objects.filter(name__icontains=query)
    
    def get_or_create_unknown(self):
        """Special Case pattern - get/create Unknown brand"""
        brand, created = self.model.objects.get_or_create(
            name='Unknown',
            defaults={'is_unknown': True}
        )
        return brand

class GuitarRepository(BaseRepository):
    model = Guitar

    def create_custom(self, brand_obj, name, specs):
        return self.model.objects.create(
            brand=brand_obj,
            name=name,
            **specs
        )
    
    def search(self, query=None, brand_id=None, limit=20):
        qs = self._get_base_queryset()
        if query:
            qs = qs.filter(name__icontains=query)
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        return qs[:limit]


class AmplifierRepository(BaseRepository):
    model = Amplifier
    
    def create_custom(self, brand_obj, name, specs):
        return self.model.objects.create(
            brand=brand_obj,
            name=name,
            **specs
        )

    def search(self, query=None, brand_id=None, limit=20):
        qs = self._get_base_queryset()
        if query:
            qs = qs.filter(name__icontains=query)
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        return qs[:limit]


class PedalRepository(BaseRepository):
    model = Pedal
    
    def create_custom(self, brand_obj, name, specs):
        return self.model.objects.create(
            brand=brand_obj,
            name=name,
            **specs
        )

    def search(self, query=None, brand_id=None, limit=20):
        qs = self._get_base_queryset()
        if query:
            qs = qs.filter(name__icontains=query)
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        return qs[:limit]

class OwnedGearRepository(BaseRepository):
    model = OwnedGear

    def filter_gear(
        self,
        gear_types=None,
        brand_id=None,
        search_query=None,
        favorites_only=False,
    ) -> QuerySet:
        """
        Universal filter method for gear with multiple criteria.
        Automatically scoped to self.user

        Args:
            gear_types: list of types ['guitar', 'amplifier'] or None (all)
            brand_id: int or None
            search_query: str or None
            favorites_only: bool
        """
        queryset = self._get_base_queryset()

        if gear_types:
            type_filters = Q()

            if "guitar" in gear_types:
                type_filters |= Q(guitar__isnull=False)
            if "amplifier" in gear_types:
                type_filters |= Q(amplifier__isnull=False)
            if "pedal" in gear_types:
                type_filters |= Q(pedal__isnull=False)

            queryset = queryset.filter(type_filters)

        if brand_id:
            queryset = queryset.filter(
                Q(guitar__brand_id=brand_id)
                | Q(amplifier__brand_id=brand_id)
                | Q(pedal__brand_id=brand_id)
            )

        if search_query:
            queryset = queryset.filter(
                Q(nickname__icontains=search_query)
                | Q(guitar__name__icontains=search_query)
                | Q(amplifier__name__icontains=search_query)
                | Q(pedal__name__icontains=search_query)
            )

        if favorites_only:
            queryset = queryset.filter(is_favorite=True)

        queryset = queryset.select_related(
            "guitar",
            "guitar__brand",
            "amplifier",
            "amplifier__brand",
            "pedal",
            "pedal__brand",
        )

        return queryset.order_by("is_favorite", "-created_at")

    def get_user_brands(self):
        """
        Returns a QuerySet of Brands that appear in the user's collection.
        Used for populating the filter dropdown.
        """
        qs = self._get_base_queryset()

        guitar_brands = qs.filter(guitar__isnull=False).values_list('guitar__brand_id', flat=True)
        amp_brands = qs.filter(amplifier__isnull=False).values_list('amplifier__brand_id', flat=True)
        pedal_brands = qs.filter(pedal__isnull=False).values_list('pedal__brand_id', flat=True)

        brand_ids = set(guitar_brands) | set(amp_brands) | set(pedal_brands)
        
        brand_ids.discard(None)

        return Brand.objects.filter(id__in=brand_ids).order_by('name')
    def get_favorites() -> QuerySet:
        return self.filter_gear(favorites_only=True)

    def count_by_type(self) -> dict[str, int]:
        base_qs = self._get_base_queryset()
        return {
            "guitars": base_qs.filter(guitar__isnull=False).count(),
            "amplifiers": base_qs.filter(amplifier__isnull=False).count(),
            "pedals": base_qs.filter(pedal__isnull=False).count(),
        }
