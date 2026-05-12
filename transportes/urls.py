from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:token>/', views.formulario_transporte, name='transporte_formulario'),
    path('<uuid:token>/confirmacion/', views.confirmacion_transporte, name='transporte_confirmacion'),
]
