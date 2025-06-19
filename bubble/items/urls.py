from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    # Main item list
    path('', views.ItemListView.as_view(), name='list'),

    # Item type filtered lists (shareable URLs)
    path('sell/', views.ItemListView.as_view(), {'item_type_filter': 0}, name='sell'),
    path('give_away/', views.ItemListView.as_view(), {'item_type_filter': 1}, name='give_away'),
    path('borrow/', views.ItemListView.as_view(), {'item_type_filter': 2}, name='borrow'),
    path('need/', views.ItemListView.as_view(), {'item_type_filter': 3}, name='need'),

    # Item detail
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detail'),

    # Item CRUD operations (login required)
    path('create/', views.ItemCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ItemUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ItemDeleteView.as_view(), name='delete'),

    # User's item management
    path('my-items/', views.MyItemsView.as_view(), name='my_items'),
    path('<int:pk>/toggle-status/', views.toggle_item_status, name='toggle_status'),
    
    # AJAX endpoints
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),
]