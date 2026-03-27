from django.core.exceptions import ObjectDoesNotExist


class BaseRepository:
    """
    Base Repository with optional user scoping.

    Repository Pattern - abstracts data access layer.
    Supports user-scoped queries for models with 'user' field.

    Usage:
        # User-scoped (only that user's data):
        repo = OwnedGearRepository(user=request.user)

        # Global (all data, e.g., for admin):
        repo = BrandRepository()
    """

    model = None
    user_field = "user"

    def __init__(self, user=None):
        self.user = user

    def _get_base_queryset(self):
        queryset = self.model.objects.all()

        if self.user and hasattr(self.model, self.user_field):
            # Filter by user if provided and model has user field
            filter_kwargs = {self.user_field: self.user}
            queryset = queryset.filter(**filter_kwargs)

        return queryset

    def get_all(self):
        return self._get_base_queryset()

    def get_by_id(self, obj_id):
        try:
            return self._get_base_queryset().get(id=obj_id)
        except ObjectDoesNotExist:
            return None

    def create(self, **kwargs):
        if (
            self.user
            and self.user_field not in kwargs
            and hasattr(self.model, self.user_field)
        ):
            kwargs[self.user_field] = self.user

        return self.model.objects.create(**kwargs)

    def update(self, obj_id, **kwargs):
        obj = self.get_by_id(obj_id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            obj.save()
            return obj
        return None

    def delete(self, obj_id) -> bool:
        obj = self.get_by_id(obj_id)
        if obj:
            obj.delete()
            return True
        return False

    def count(self):
        return self._get_base_queryset().count()

    def exists(self, **kwargs):
        return self._get_base_queryset().filter(**kwargs).exists()
