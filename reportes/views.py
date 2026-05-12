from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from core.models import Pernoctacion
import logging

logger = logging.getLogger(__name__)


def _calcular_kpis(pernoctaciones):
    total = pernoctaciones.count()
    if total == 0:
        return {}

    cumple_00h     = pernoctaciones.filter(cumple_00h=True).count()
    no_cumple_00h  = pernoctaciones.filter(cumple_00h=False).count()
    en_ruta_00h    = pernoctaciones.filter(cumple_00h__isnull=True).count()
    sin_senal      = pernoctaciones.filter(sin_senal=True).count()
    con_extension  = pernoctaciones.filter(extension_horaria=True).count()

    cumple_8h      = pernoctaciones.filter(cumple_8h=True).count()
    no_cumple_8h   = pernoctaciones.filter(cumple_8h=False).count()
    en_ruta_8h     = pernoctaciones.filter(cumple_8h__isnull=True).count()

    base_00h = cumple_00h + no_cumple_00h
    base_8h  = cumple_8h + no_cumple_8h

    pct_00h = round(cumple_00h / base_00h * 100, 1) if base_00h else 0
    pct_8h  = round(cumple_8h  / base_8h  * 100, 1) if base_8h  else 0

    # Agrupar por transporte
    transportes = {}
    for p in pernoctaciones:
        tte = p.transporte_nombre
        if tte not in transportes:
            transportes[tte] = {
                'nombre': tte,
                'total': 0,
                'cumple_00h': 0,
                'no_cumple_00h': 0,
                'cumple_8h': 0,
                'no_cumple_8h': 0,
                'sin_senal': 0,
            }
        transportes[tte]['total'] += 1
        if p.cumple_00h is True:  transportes[tte]['cumple_00h'] += 1
        if p.cumple_00h is False: transportes[tte]['no_cumple_00h'] += 1
        if p.cumple_8h is True:   transportes[tte]['cumple_8h'] += 1
        if p.cumple_8h is False:  transportes[tte]['no_cumple_8h'] += 1
        if p.sin_senal:           transportes[tte]['sin_senal'] += 1

    return {
        'total': total,
        'cumple_00h': cumple_00h,
        'no_cumple_00h': no_cumple_00h,
        'en_ruta_00h': en_ruta_00h,
        'sin_senal': sin_senal,
        'con_extension': con_extension,
        'cumple_8h': cumple_8h,
        'no_cumple_8h': no_cumple_8h,
        'en_ruta_8h': en_ruta_8h,
        'pct_00h': pct_00h,
        'pct_8h': pct_8h,
        'transportes': list(transportes.values()),
    }


@login_required
def reporte_cierre(request):
    hoy = timezone.localdate()
    pernoctaciones = Pernoctacion.objects.filter(fecha_registro=hoy).order_by('transporte_nombre', 'patente')
    kpis = _calcular_kpis(pernoctaciones)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'enviar_reporte':
            emails_raw = request.POST.get('emails_destino', '').strip()
            emails = [e.strip() for e in emails_raw.replace(';', ',').split(',') if e.strip()]

            if not emails:
                messages.error(request, 'Ingresa al menos un email de destino.')
                return redirect('reporte_cierre')

            turno = request.POST.get('turno', 'Turno')

            try:
                html_content = render_to_string('reportes/email_cierre.html', {
                    'kpis': kpis,
                    'pernoctaciones': pernoctaciones,
                    'fecha': hoy,
                    'turno': turno,
                    'enviado_por': request.user.get_full_name() or request.user.username,
                })

                text_content = (
                    f"REPORTE DE PERNOCTACIONES — {hoy.strftime('%d/%m/%Y')} — {turno}\n\n"
                    f"TOTAL EQUIPOS: {kpis.get('total', 0)}\n\n"
                    f"DETENCIÓN ANTES 00:00\n"
                    f"  CUMPLE:   {kpis.get('cumple_00h', 0)}\n"
                    f"  NO CUMPLE: {kpis.get('no_cumple_00h', 0)}\n"
                    f"  EN RUTA:  {kpis.get('en_ruta_00h', 0)}\n"
                    f"  % CUMPLIMIENTO: {kpis.get('pct_00h', 0)}%\n\n"
                    f"CUMPLIMIENTO 8 HORAS\n"
                    f"  CUMPLE:   {kpis.get('cumple_8h', 0)}\n"
                    f"  NO CUMPLE: {kpis.get('no_cumple_8h', 0)}\n"
                    f"  EN RUTA:  {kpis.get('en_ruta_8h', 0)}\n"
                    f"  % CUMPLIMIENTO: {kpis.get('pct_8h', 0)}%\n"
                )

                msg = EmailMultiAlternatives(
                    subject=f"Reporte Pernoctaciones {hoy.strftime('%d/%m/%Y')} — {turno}",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=emails,
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                messages.success(request, f'Reporte enviado a: {", ".join(emails)}')

            except Exception as e:
                logger.error(f"Error enviando reporte: {e}")
                messages.error(request, f'Error al enviar: {str(e)}')

            return redirect('reporte_cierre')

    email_jefatura = getattr(settings, 'EMAIL_JEFATURA', '')

    context = {
        'kpis': kpis,
        'pernoctaciones': pernoctaciones,
        'hoy': hoy,
        'email_jefatura': email_jefatura,
    }
    return render(request, 'reportes/cierre.html', context)
