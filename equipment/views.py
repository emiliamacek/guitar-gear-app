from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views.generic import CreateView, ListView, TemplateView, View, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages

from .models import OwnedGear, Guitar, Amplifier, Pedal, GearRequest
from .forms import GuitarAddForm, AmplifierAddForm, PedalAddForm
from .services import EquipmentService
from .repositories import OwnedGearRepository, GuitarRepository, AmplifierRepository, PedalRepository, BrandRepository

User = get_user_model()

class AddGearOptionsView(LoginRequiredMixin, TemplateView):
    template_name = "equipment/add_options.html"


class AddCustomGearView(LoginRequiredMixin, CreateView):
    """
    Universal view for adding custom gear
    """
    template_name = "equipment/add_custom.html"
    success_url = reverse_lazy("equipment:list")

    def dispatch(self, request, *args, **kwargs):
        # get gear type from URL (e.g. /equipment/add/guitar/)
        self.gear_type = kwargs.get('gear_type')
        if self.gear_type not in ['guitar', 'amplifier', 'pedal']:
            messages.error(request, "Unknown gear type!")
            return redirect("equipment:list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if self.gear_type == 'guitar':
            return GuitarAddForm
        elif self.gear_type == 'amplifier':
            return AmplifierAddForm
        elif self.gear_type == 'pedal':
            return PedalAddForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gear_type'] = self.gear_type.capitalize()
        return context

    def form_valid(self, form):
        service = EquipmentService(user=self.request.user)
        
        cleaned_data = form.cleaned_data
        
        ownership_data = {
            'nickname': cleaned_data.pop('nickname', ''),
            'serial_number': cleaned_data.pop('serial_number', ''),
            'is_favorite': cleaned_data.pop('is_favorite', False)
        }
        
        name = cleaned_data.pop('name')
        specs = cleaned_data
        
        try:
            service.add_custom_gear(
                gear_type=self.gear_type,
                name=name,
                specs=specs,
                ownership_data=ownership_data
            )
            messages.success(self.request, f"Custom {self.gear_type} added to your collection!")
            return redirect(self.success_url)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)



class OwnedGearListView(LoginRequiredMixin, ListView):
    model = OwnedGear
    template_name = "equipment/list.html"
    context_object_name = "gear_list"

    def get_queryset(self):
        repo = OwnedGearRepository(user=self.request.user)
        return repo.filter_gear(
            gear_types=self.request.GET.getlist("type"),
            brand_id=self.request.GET.get("brand"),
            search_query=self.request.GET.get("q"),
            favorites_only=self.request.GET.get("favorites") == "true",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        repo = OwnedGearRepository(user=self.request.user)
        
        context["gear_stats"] = repo.count_by_type()
        
        context['brands'] = repo.get_user_brands()

        context["active_filters"] = {
            "types": self.request.GET.getlist("type"),
            "brand": self.request.GET.get("brand"),
            "search": self.request.GET.get("q"),
            "favorites": self.request.GET.get("favorites") == "true",
        }
        return context

class CatalogSearchView(LoginRequiredMixin, ListView):
    template_name = 'equipment/catalog_search.html'
    context_object_name = 'results'

    def get_queryset(self):
        query = self.request.GET.get('q')
        gear_type = self.request.GET.get('type')   # 'guitar', 'amplifier', 'pedal'
        brand_id = self.request.GET.get('brand')   

        results = []
        
        guitar_repo = GuitarRepository()
        amp_repo = AmplifierRepository()
        pedal_repo = PedalRepository()

        search_guitars = gear_type == 'guitar' or not gear_type
        search_amps = gear_type == 'amplifier' or not gear_type
        search_pedals = gear_type == 'pedal' or not gear_type

        if search_guitars:
            guitars = guitar_repo.search(query=query, brand_id=brand_id)
            for g in guitars:
                g.type = 'guitar' 
                results.append(g)

        if search_amps:
            amps = amp_repo.search(query=query, brand_id=brand_id)
            for a in amps:
                a.type = 'amplifier'
                results.append(a)

        if search_pedals:
            pedals = pedal_repo.search(query=query, brand_id=brand_id)
            for p in pedals:
                p.type = 'pedal'
                results.append(p)
                
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        brand_repo = BrandRepository()
        context['brands'] = brand_repo.get_all().order_by('name')
        
        context['active_brand'] = self.request.GET.get('brand')
        context['active_type'] = self.request.GET.get('type')
        context['search_query'] = self.request.GET.get('q', '')
        return context
class AddFromCatalogView(LoginRequiredMixin, View):
    def post(self, request, gear_type, pk):
        service = EquipmentService(user=request.user)
        
        ownership_data = {
            'nickname': '',
            'serial_number': '',
            'is_favorite': False
        }
        
        try:
            service.add_existing_gear_to_collection(gear_type, pk, ownership_data)
            messages.success(request, "Gear added to your collection!")
        except Exception as e:
            messages.error(request, f"Error adding gear: {e}")
            
        return redirect('equipment:list')

class GearRequestCreateView(LoginRequiredMixin, CreateView):
    model = GearRequest
    fields = ['gear_type', 'brand_name', 'model_name']
    template_name = 'equipment/request_gear.html'
    success_url = reverse_lazy('equipment:catalog_search')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Request sent to admins! We'll add it soon.")
        return super().form_valid(form)

class OwnedGearDetailView(LoginRequiredMixin, DetailView):
    model = OwnedGear
    template_name = 'equipment/detail.html'
    context_object_name = 'gear'

    def test_func(self):
        gear = self.get_object()
        return self.request.user == gear.user


class OwnedGearUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit only (nickname, serial number, ulubione).
    User can't edit brand/model
    """
    model = OwnedGear
    fields = ['nickname', 'serial_number', 'is_favorite']
    template_name = 'equipment/form.html'
    success_url = reverse_lazy('equipment:list')

    def test_func(self):
        return self.request.user == self.get_object().user
    
    def form_valid(self, form):
        messages.success(self.request, "Gear details updated!")
        return super().form_valid(form)


class OwnedGearDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = OwnedGear
    template_name = 'equipment/confirm_delete.html'
    success_url = reverse_lazy('equipment:list')

    def test_func(self):
        return self.request.user == self.get_object().user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Gear removed from your collection.")
        return super().delete(request, *args, **kwargs)

class PublicUserGearListView(LoginRequiredMixin, ListView):
    model = OwnedGear
    template_name = "equipment/public_list.html"
    context_object_name = "gear_list"

    def get_queryset(self):
        self.viewed_user = get_object_or_404(User, username=self.kwargs['username'])
        repo = OwnedGearRepository(user=self.viewed_user)
        return repo.get_all().select_related(
            'guitar', 
            'guitar__brand',
            'amplifier', 
            'amplifier__brand',  
            'pedal', 
            'pedal__brand'       
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['viewed_user'] = self.viewed_user
        return context
