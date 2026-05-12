from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time, timedelta
from core.models import Pernoctacion


@login_required
def validacion_primera(request):
    """
    Turno noche — Validar si el equipo llegó antes de las 00:00 hrs.
    También permite asignar extensión horaria si viene con atraso.
    """
    hoy = timezone.localdate()

    # Equipos que ya tienen lugar confirmado pero aún no tienen validación de llegada
    equipos = Pernoctacion.objects.filter(
        fecha_registro=hoy,
        estado='CONFIRMADO',
        cumple_00h__isnull=True,
    ).order_by('transporte_nombre', 'patente')

    # Equipos ya validados hoy (para referencia)
    ya_validados = Pernoctacion.objects.filter(
        fecha_registro=hoy,
        cumple_00h__isnull=False,
    ).order_by('transporte_nombre')

    if request.method == 'POST':
        procesados = 0

        for equipo in Pernoctacion.objects.filter(fecha_registro=hoy, estado='CONFIRMADO'):
            accion = request.POST.get(f'accion_{equipo.id}')
            if not accion:
                continue

            hora_llegada_str = request.POST.get(f'hora_llegada_{equipo.id}', '').strip()
            extension = request.POST.get(f'extension_{equipo.id}') == 'on'
            observacion = request.POST.get(f'obs_{equipo.id}', '').strip()
            sin_senal = request.POST.get(f'sin_senal_{equipo.id}') == 'on'

            # Parsear hora de llegada
            hora_llegada_dt = None
            if hora_llegada_str:
                try:
                    partes = hora_llegada_str.split(':')
                    h, m = int(partes[0]), int(partes[1])
                    # Si la hora es entre 00:00 y 06:00 se asume que es del día siguiente
                    fecha_base = hoy
                    if h < 6:
                        fecha_base = hoy + timedelta(days=1)
                    hora_llegada_dt = timezone.make_aware(
                        datetime.combine(fecha_base, time(h, m))
                    )
                except (ValueError, IndexError):
                    hora_llegada_dt = None

            if accion == 'cumple':
                equipo.cumple_00h = True
                equipo.extension_horaria = False
            elif accion == 'no_cumple':
                equipo.cumple_00h = False
                equipo.extension_horaria = extension
            elif accion == 'sin_senal':
                equipo.sin_senal = True
                equipo.cumple_00h = None  # queda pendiente
                equipo.observaciones_primera = observacion
                equipo.validado_primera_por = request.user
                equipo.save()
                procesados += 1
                continue

            equipo.hora_llegada_real = hora_llegada_dt
            equipo.observaciones_primera = observacion
            equipo.validado_primera_por = request.user
            equipo.estado = 'VALIDADO_1'
            equipo.save()
            procesados += 1

        if procesados:
            messages.success(request, f'{procesados} equipo(s) validados correctamente.')
        return redirect('validacion_primera')

    context = {
        'equipos': equipos,
        'ya_validados': ya_validados,
        'hoy': hoy,
        'total_pendientes': equipos.count(),
        'total_validados': ya_validados.count(),
    }
    return render(request, 'validacion/primera.html', context)


@login_required
def validacion_ocho(request):
    """
    Turno noche — Validar cumplimiento de 8 horas de descanso.
    Ingresa la hora de salida del equipo.
    """
    hoy = timezone.localdate()

    equipos = Pernoctacion.objects.filter(
        fecha_registro=hoy,
        estado='VALIDADO_1',
        cumple_00h=True,
        cumple_8h__isnull=True,
    ).order_by('transporte_nombre', 'patente')

    ya_validados = Pernoctacion.objects.filter(
        fecha_registro=hoy,
        cumple_8h__isnull=False,
    ).order_by('transporte_nombre')

    if request.method == 'POST':
        procesados = 0

        for equipo in Pernoctacion.objects.filter(fecha_registro=hoy, estado='VALIDADO_1', cumple_00h=True):
            hora_salida_str = request.POST.get(f'hora_salida_{equipo.id}', '').strip()
            observacion = request.POST.get(f'obs_{equipo.id}', '').strip()

            if not hora_salida_str:
                continue

            try:
                partes = hora_salida_str.split(':')
                h, m = int(partes[0]), int(partes[1])
                # Hora salida es el día siguiente (turno mañana)
                fecha_salida = hoy + timedelta(days=1)
                hora_salida_dt = timezone.make_aware(
                    datetime.combine(fecha_salida, time(h, m))
                )
            except (ValueError, IndexError):
                messages.error(request, f'Hora inválida para {equipo.patente}')
                continue

            equipo.hora_salida = hora_salida_dt
            equipo.observaciones_segunda = observacion

            # Calcular horas totales
            if equipo.hora_llegada_real:
                delta = hora_salida_dt - equipo.hora_llegada_real
                equipo.horas_totales = delta
                horas = delta.total_seconds() / 3600
                equipo.cumple_8h = horas >= 8
            else:
                # Si no hay hora llegada, evaluar manualmente
                accion = request.POST.get(f'accion_8h_{equipo.id}')
                equipo.cumple_8h = (accion == 'cumple')

            equipo.validado_segunda_por = request.user
            equipo.estado = 'VALIDADO_2'
            equipo.save()
            procesados += 1

        if procesados:
            messages.success(request, f'{procesados} equipo(s) con 8 horas validadas.')
        return redirect('validacion_ocho')

    context = {
        'equipos': equipos,
        'ya_validados': ya_validados,
        'hoy': hoy,
        'total_pendientes': equipos.count(),
        'total_validados': ya_validados.count(),
    }
    return render(request, 'validacion/ocho.html', context)


@login_required
def validacion_detalle(request, pk):
    """Vista de detalle y edición de una pernoctación específica."""
    pernoctacion = get_object_or_404(Pernoctacion, pk=pk)
    hoy = timezone.localdate()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'actualizar_lugar':
            pernoctacion.lugar_pernoctacion = request.POST.get('lugar', '').strip()
            hora_eta_str = request.POST.get('hora_eta', '').strip()
            if hora_eta_str:
                try:
                    partes = hora_eta_str.split(':')
                    from datetime import time as dtime
                    pernoctacion.hora_eta = dtime(int(partes[0]), int(partes[1]))
                except Exception:
                    pass
            pernoctacion.save()
            messages.success(request, 'Lugar actualizado.')

        elif accion == 'marcar_sin_senal':
            pernoctacion.sin_senal = not pernoctacion.sin_senal
            pernoctacion.save()
            estado = 'Sin señal activado' if pernoctacion.sin_senal else 'Sin señal desactivado'
            messages.info(request, estado)

        return redirect('validacion_detalle', pk=pk)

    context = {'p': pernoctacion, 'hoy': hoy}
    return render(request, 'validacion/detalle.html', context)
