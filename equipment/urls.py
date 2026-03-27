from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    path('', views.OwnedGearListView.as_view(), name='list'),
    path('add-options/', views.AddGearOptionsView.as_view(), name='add_options'),
    
    path('add/custom/<str:gear_type>/', views.AddCustomGearView.as_view(), name='add_custom'),
    
    path('catalog/', views.CatalogSearchView.as_view(), name='catalog_search'),
    path('catalog/add/<str:gear_type>/<int:pk>/', views.AddFromCatalogView.as_view(), name='catalog_add'),
    path('request/', views.GearRequestCreateView.as_view(), name='request_gear'),

    path('gear/<int:pk>/', views.OwnedGearDetailView.as_view(), name='detail'),
    path('gear/<int:pk>/edit/', views.OwnedGearUpdateView.as_view(), name='update'),
    path('gear/<int:pk>/delete/', views.OwnedGearDeleteView.as_view(), name='delete'),
    path('user/<str:username>/', views.PublicUserGearListView.as_view(), name='public_list'),
]
