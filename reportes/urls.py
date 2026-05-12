from django.urls import path
from . import views

urlpatterns = [
    path('cierre/', views.reporte_cierre, name='reporte_cierre'),
]
