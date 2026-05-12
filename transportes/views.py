from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from core.models import Pernoctacion


def formulario_transporte(request, token):
    """
    Página pública accesible con el token del mail.
    Muestra TODOS los equipos del transporte para ese día
    y permite completar lugar + hora estimada de llegada.
    """
    # Buscar la pernoctación por token
    pernoctacion_base = get_object_or_404(Pernoctacion, token=token)
    hoy = timezone.localdate()

    # Obtener todos los equipos del mismo transporte del mismo día
    equipos = Pernoctacion.objects.filter(
        transporte_nombre=pernoctacion_base.transporte_nombre,
        fecha_registro=hoy,
    ).order_by('patente')

    if not equipos.exists():
        raise Http404("No se encontraron equipos para este enlace.")

    # Verificar si ya respondieron todos
    todos_respondidos = all(e.lugar_pernoctacion for e in equipos)

    if request.method == 'POST':
        errores = 0
        guardados = 0

        for equipo in equipos:
            lugar = request.POST.get(f'lugar_{equipo.id}', '').strip()
            hora_eta_str = request.POST.get(f'eta_{equipo.id}', '').strip()
            observacion = request.POST.get(f'obs_{equipo.id}', '').strip()
            sin_senal = request.POST.get(f'sin_senal_{equipo.id}') == 'on'

            if not lugar and not sin_senal:
                errores += 1
                continue

            # Parsear hora ETA
            hora_eta = None
            if hora_eta_str:
                try:
                    from datetime import time
                    partes = hora_eta_str.split(':')
                    hora_eta = time(int(partes[0]), int(partes[1]))
                except (ValueError, IndexError):
                    hora_eta = None

            equipo.lugar_pernoctacion = lugar
            equipo.hora_eta = hora_eta
            equipo.sin_senal = sin_senal
            equipo.observaciones_primera = observacion
            equipo.respondido_en = timezone.now()
            equipo.estado = 'CONFIRMADO'
            equipo.save()
            guardados += 1

        if errores:
            messages.warning(
                request,
                f'{errores} equipo(s) sin lugar ingresado. Completa todos o marca "Sin señal".'
            )
        if guardados:
            messages.success(
                request,
                f'✅ Información guardada correctamente para {guardados} equipo(s). ¡Gracias!'
            )
            return redirect('transporte_confirmacion', token=token)

    context = {
        'equipos': equipos,
        'transporte_nombre': pernoctacion_base.transporte_nombre,
        'hoy': hoy,
        'todos_respondidos': todos_respondidos,
        'token': token,
    }
    return render(request, 'transportes/formulario.html', context)


def confirmacion_transporte(request, token):
    """Página de agradecimiento tras enviar los datos."""
    pernoctacion_base = get_object_or_404(Pernoctacion, token=token)
    hoy = timezone.localdate()

    equipos = Pernoctacion.objects.filter(
        transporte_nombre=pernoctacion_base.transporte_nombre,
        fecha_registro=hoy,
    ).order_by('patente')

    context = {
        'equipos': equipos,
        'transporte_nombre': pernoctacion_base.transporte_nombre,
        'hoy': hoy,
        'token': token,
    }
    return render(request, 'transportes/confirmacion.html', context)
