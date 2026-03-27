from django.views.generic import TemplateView
import equipment
from setups.models import Setup
from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from equipment.models import OwnedGear
from setups.services import SetupService

from equipment.services import EquipmentService
from equipment.repositories import OwnedGearRepository

User = get_user_model()

class UserProfileView(DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        viewed_user = self.object 
        is_own_profile = (self.request.user == viewed_user)

        setup_service = SetupService(user=viewed_user)
        equipment_service = EquipmentService(user=viewed_user)
        
        stats = equipment_service.get_statistics()
        context['gear_stats'] = stats if stats else {}
        context['gear_total'] = sum(context['gear_stats'].values())
        
        if is_own_profile:
            all_setups = setup_service.get_user_setups()
        else:
            all_setups = setup_service.get_public_setups().filter(user=viewed_user)
            
        context['total_setups_count'] = all_setups.count()
        context['recent_setups'] = all_setups.order_by('-created_at')[:3] 
        
        gear_repo = OwnedGearRepository(user=viewed_user)
        all_gear = gear_repo.get_all()
        
        context['total_gear_count'] = all_gear.count()
        
        context['recent_gear'] = all_gear.select_related(
            'guitar', 'guitar__brand', 
            'amplifier', 'amplifier__brand', 
            'pedal', 'pedal__brand'
        ).order_by('-created_at')[:4]

        context['is_own_profile'] = is_own_profile
        
        return context

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user if self.request.user.is_authenticated else None
        service = SetupService(user=user)

        qs = service.get_public_setups()

        context['latest_setups'] = qs.order_by('-created_at')[:3]
        return context
