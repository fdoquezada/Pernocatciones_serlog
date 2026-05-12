import json
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import CargaTMS, Pernoctacion, Transporte
from .processor import procesar_tms, extraer_campos_pernoctacion


def _parse_fecha(s):
    if not s or s == 'None':
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None

def _parse_datetime(s):
    if not s or s == 'None':
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None



@login_required
def cargar_tms(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')

        if not archivo:
            messages.error(request, 'Debes seleccionar un archivo.')
            return redirect('tms_cargar')

        if not archivo.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls).')
            return redirect('tms_cargar')

        try:
            df = procesar_tms(archivo)

            total_original = df.attrs.get('total_original', 0)
            total_filtrado = df.attrs.get('total_filtrado', 0)

            registros = extraer_campos_pernoctacion(df)
            request.session['tms_registros'] = registros
            request.session['tms_total_original'] = total_original
            request.session['tms_total_filtrado'] = total_filtrado
            request.session['tms_archivo_nombre'] = archivo.name

            archivo.seek(0)
            carga = CargaTMS.objects.create(
                archivo=archivo,
                subido_por=request.user,
                total_registros=total_original,
                total_filtrados=total_filtrado,
            )
            request.session['tms_carga_id'] = carga.id

            messages.success(
                request,
                f'Archivo procesado: {total_original} registros originales → {total_filtrado} después de filtros.'
            )
            return redirect('tms_revision')

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return redirect('tms_cargar')

    return render(request, 'tms/cargar.html')


@login_required
def revision_tms(request):
    registros = request.session.get('tms_registros')

    if not registros:
        messages.warning(request, 'No hay datos cargados. Sube el archivo TMS primero.')
        return redirect('tms_cargar')

    total_original = request.session.get('tms_total_original', 0)
    total_filtrado = request.session.get('tms_total_filtrado', 0)
    archivo_nombre = request.session.get('tms_archivo_nombre', '')

    transportes = {}
    for r in registros:
        tte = r['transporte_nombre']
        if tte not in transportes:
            transportes[tte] = []
        transportes[tte].append(r)

    context = {
        'registros': registros,
        'transportes': transportes,
        'total_original': total_original,
        'total_filtrado': total_filtrado,
        'archivo_nombre': archivo_nombre,
        'total_transportes': len(transportes),
    }
    return render(request, 'tms/revision.html', context)


@login_required
def confirmar_carga(request):
    if request.method != 'POST':
        return redirect('tms_revision')

    registros = request.session.get('tms_registros')
    carga_id = request.session.get('tms_carga_id')

    if not registros:
        messages.error(request, 'No hay datos en sesión. Recarga el archivo.')
        return redirect('tms_cargar')

    seleccionados = request.POST.getlist('seleccionados')
    if not seleccionados:
        seleccionados = [str(i) for i in range(len(registros))]

    hoy = timezone.localdate()
    carga = CargaTMS.objects.filter(id=carga_id).first()

    creados = 0
    for idx in seleccionados:
        try:
            r = registros[int(idx)]
        except (IndexError, ValueError):
            continue

        transporte_obj, _ = Transporte.objects.get_or_create(
            nombre=r['transporte_nombre'],
            defaults={'email': '', 'activo': True}
        )

        existe = Pernoctacion.objects.filter(
            patente=r['patente'],
            fecha_registro=hoy,
            id_viaje=r['id_viaje'],
        ).exists()

        if not existe:
            Pernoctacion.objects.create(
                carga=carga,
                id_pedido=r['id_pedido'],
                id_viaje=r['id_viaje'],
                cliente=r['cliente'],
                transporte=transporte_obj,
                transporte_nombre=r['transporte_nombre'],
                patente=r['patente'],
                patente_secundaria=r.get('patente_secundaria', ''),
                conductor=r['conductor'],
                fecha_inicio_plan=_parse_datetime(r.get('fecha_inicio_plan')),
                fecha_fin_plan=_parse_fecha(r.get('fecha_fin_plan')),
                fecha_plan_descarga=_parse_fecha(r.get('fecha_plan_descarga')),
                direccion_descarga=r.get('direccion_descarga', ''),
                operacion=r.get('operacion', ''),
                categoria=r.get('categoria', ''),
            )
            creados += 1

    for key in ['tms_registros', 'tms_total_original', 'tms_total_filtrado',
                'tms_archivo_nombre', 'tms_carga_id']:
        request.session.pop(key, None)

    messages.success(request, f'{creados} pernoctaciones registradas correctamente.')
    return redirect('notificaciones_enviar')
