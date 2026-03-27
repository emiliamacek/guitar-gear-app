from django.urls import path
from . import views

app_name = 'setups'

urlpatterns = [
    path('', views.SetupListView.as_view(), name='list'),
    path('create/', views.SetupCreateView.as_view(), name='create'),
    path('community/', views.CommunitySetupsView.as_view(), name='community'),
    path('saved/', views.SavedSetupsListView.as_view(), name='saved'),

    path('<int:pk>/', views.SetupDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SetupUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SetupDeleteView.as_view(), name='delete'),

    path('<int:setup_id>/remove/<int:item_id>/', views.RemoveGearFromSetupView.as_view(), name='remove_gear'),
    path('<int:setup_id>/toggle-favorite/', views.ToggleSetupFavoriteView.as_view(), name='toggle_favorite'),
    path('<int:setup_id>/toggle-public/', views.ToggleSetupPublicView.as_view(), name='toggle_public'),
    path('<int:setup_id>/toggle-save/', views.ToggleSetupSaveView.as_view(), name='toggle_save'),
]
