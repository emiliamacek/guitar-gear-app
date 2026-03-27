from django.views.generic import CreateView, DetailView, ListView, View, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from setups.models import Setup, Genre, Song, Band
from setups.forms import SetupForm, AddGearToSetupForm
from setups.services import SetupService


class SetupCreateView(LoginRequiredMixin, CreateView):
    """Create Setup using Service Layer"""
    model = Setup
    form_class = SetupForm
    template_name = 'setups/create.html'
    
    def form_valid(self, form):
        service = SetupService(user=self.request.user)
        
        try:
            setup = service.create_setup(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                genre=form.cleaned_data.get('genre'),
                band=form.cleaned_data.get('band'),
                song=form.cleaned_data.get('song'),
                is_public=form.cleaned_data.get('is_public', False)
            )
            
            messages.success(
                self.request, 
                f'Setup "{setup.name}" created! Now add gear to the signal chain.'
            )
            return redirect('setups:detail', pk=setup.pk)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class SetupDetailView(LoginRequiredMixin, DetailView):
    """View setup with signal chain"""
    model = Setup
    template_name = 'setups/detail.html'
    context_object_name = 'setup'
    
    def get_object(self):
        service = SetupService(user=self.request.user)
        setup = service.get_setup_with_chain(self.kwargs['pk'])
        
        if not setup:
            from django.http import Http404
            raise Http404("Setup not found")
            
        # Increment views (exclude user enters)
        if self.request.user != setup.user:
            service.increment_views(setup.id)
        
        return setup
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['add_gear_form'] = AddGearToSetupForm(user=self.request.user)
        
        # Signal chain (already prefetched by service)
        context['signal_chain'] = self.object.signal_chain.all()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle inline add gear form"""
        self.object = self.get_object()
        form = AddGearToSetupForm(request.POST, user=request.user)
        
        if form.is_valid():
            service = SetupService(user=request.user)
            
            try:
                item = service.add_gear_to_setup(
                    setup_id=self.object.id,
                    owned_gear_id=form.cleaned_data['owned_gear'].id,
                    order=form.cleaned_data.get('order'),
                    settings=form.cleaned_data.get('settings', {}),
                    notes=form.cleaned_data.get('notes', '')
                )
                
                messages.success(
                    request, 
                    f'Added {item.owned_gear} to signal chain!'
                )
                return redirect('setups:detail', pk=self.object.pk)
                
            except ValueError as e:
                messages.error(request, str(e))
        
        # If form invalid, re-render with errors
        context = self.get_context_data()
        context['add_gear_form'] = form
        return self.render_to_response(context)

class SetupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    User can only edit their own setup
    """
    model = Setup
    form_class = SetupForm
    template_name = 'setups/edit.html'
    context_object_name = 'setup'

    def test_func(self):
        setup = self.get_object()
        return self.request.user == setup.user

    def get_success_url(self):
        messages.success(self.request, "Setup updated successfully!")
        return reverse('setups:detail', kwargs={'pk': self.object.pk})

class SetupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete setup logic
    """
    model = Setup
    template_name = 'setups/confirm_delete.html'
    success_url = reverse_lazy('setups:list')

    def test_func(self):
        setup = self.get_object()
        return self.request.user == setup.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Setup deleted successfully.")
        return super().delete(request, *args, **kwargs)

class RemoveGearFromSetupView(LoginRequiredMixin, View):
    def post(self, request, setup_id, item_id):
        service = SetupService(user=request.user)
        
        try:
            service.remove_gear_from_setup(setup_id, item_id)
            messages.success(request, 'Gear removed from signal chain!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('setups:detail', pk=setup_id)


class SetupListView(LoginRequiredMixin, ListView):
    model = Setup
    template_name = 'setups/list.html'
    context_object_name = 'setups'
    
    def get_queryset(self):
        service = SetupService(user=self.request.user)
        return service.get_user_setups()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = SetupService(user=self.request.user)
        context['setup_stats'] = service.get_statistics()
        return context


class CommunitySetupsView(ListView):
    """Community page - public setups"""
    model = Setup
    template_name = 'setups/community.html'
    context_object_name = 'setups'
    paginate_by = 20
    
    def get_queryset(self):
        service = SetupService(user=self.request.user if self.request.user.is_authenticated else None)
        return service.get_public_setups(
            genre=self.request.GET.get('genre'),
            band=self.request.GET.get('band'),
            song=self.request.GET.get('song'),
            search_query=self.request.GET.get('q'),
            author_username=self.request.GET.get('author') 
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        genre_id = self.request.GET.get('genre')
        band_id = self.request.GET.get('band')
        song_id = self.request.GET.get('song')

        if song_id:
            selected_song = Song.objects.filter(id=song_id).select_related('band', 'band__genre').first()
            
            if selected_song:
                if not band_id or band_id != str(selected_song.band.id):
                    band_id = str(selected_song.band.id)
                
                if not genre_id or genre_id != str(selected_song.band.genre.id):
                    genre_id = str(selected_song.band.genre.id)

        if band_id and not genre_id:
            selected_band = Band.objects.filter(id=band_id).select_related('genre').first()
            if selected_band:
                genre_id = str(selected_band.genre.id)

        if genre_id and band_id:
            if not Band.objects.filter(id=band_id, genre_id=genre_id).exists():
                band_id = None
                song_id = None 

        if band_id and song_id:
            if not Song.objects.filter(id=song_id, band_id=band_id).exists():
                song_id = None

        genres = Genre.objects.all().order_by('name')
        bands = Band.objects.all().order_by('name')
        songs = Song.objects.select_related('band').all().order_by('band__name', 'title')

        if genre_id:
            bands = bands.filter(genre_id=genre_id)

        if band_id:
            songs = songs.filter(band_id=band_id)
        elif genre_id:
            songs = songs.filter(band__genre_id=genre_id)

        context['genres'] = genres
        context['bands'] = bands
        context['songs'] = songs
        
        context['active_filters'] = {
            'genre': genre_id, 
            'band': band_id,
            'song': song_id,
            'search': self.request.GET.get('q'),
        }
        
        return context


class ToggleSetupFavoriteView(LoginRequiredMixin, View):
    def post(self, request, setup_id):
        service = SetupService(user=request.user)
        
        try:
            setup = service.toggle_favorite(setup_id)
            status = 'added to' if setup.is_favorite else 'removed from'
            messages.success(request, f'Setup {status} favorites!')
        except ValueError as e:
            messages.error(request, str(e))
        
        next_url = request.META.get('HTTP_REFERER', reverse('setups:list'))
        return redirect(next_url)


class ToggleSetupPublicView(LoginRequiredMixin, View):
    def post(self, request, setup_id):
        service = SetupService(user=request.user)
        
        try:
            setup = service.setup_repo.toggle_public(setup_id)
            status = 'public' if setup.is_public else 'private'
            messages.success(request, f'Setup is now {status}!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('setups:detail', pk=setup_id)

class ToggleSetupSaveView(LoginRequiredMixin, View):
    def post(self, request, setup_id):
        service = SetupService(user=request.user)
        service.toggle_save_setup(setup_id)
        # Back to the site where we where
        return redirect(request.META.get('HTTP_REFERER', 'setups:community'))

class SavedSetupsListView(LoginRequiredMixin, ListView):
    model = Setup
    template_name = 'setups/saved_list.html'
    context_object_name = 'setups'

    def get_queryset(self):
        service = SetupService(user=self.request.user)
        return service.get_saved_setups()
