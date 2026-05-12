from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def enviar_notificaciones(request):
    # Vista básica para enviar notificaciones
    # TODO: Implementar lógica de envío de notificaciones
    messages.info(request, 'Funcionalidad de envío de notificaciones en desarrollo.')
    return redirect('dashboard')
