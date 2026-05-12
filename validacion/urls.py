from django.urls import path
from . import views

urlpatterns = [
    path('primera/', views.validacion_primera, name='validacion_primera'),
    path('ocho-horas/', views.validacion_ocho, name='validacion_ocho'),
    path('detalle/<int:pk>/', views.validacion_detalle, name='validacion_detalle'),
]
