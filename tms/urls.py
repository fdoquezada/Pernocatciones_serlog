from django.urls import path
from . import views

urlpatterns = [
    path('cargar/', views.cargar_tms, name='tms_cargar'),
    path('revision/', views.revision_tms, name='tms_revision'),
    path('confirmar/', views.confirmar_carga, name='tms_confirmar'),
]