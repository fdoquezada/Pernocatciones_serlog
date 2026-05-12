from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Pernoctacion, CargaTMS


@login_required
def dashboard(request):
    hoy = timezone.localdate()

    # Estadísticas del día
    pernoctaciones_hoy = Pernoctacion.objects.filter(fecha_registro=hoy)
    total = pernoctaciones_hoy.count()
    pendientes = pernoctaciones_hoy.filter(estado='PENDIENTE').count()
    confirmados = pernoctaciones_hoy.filter(estado='CONFIRMADO').count()
    cumple_00h = pernoctaciones_hoy.filter(cumple_00h=True).count()
    no_cumple_00h = pernoctaciones_hoy.filter(cumple_00h=False).count()
    cumple_8h = pernoctaciones_hoy.filter(cumple_8h=True).count()
    no_cumple_8h = pernoctaciones_hoy.filter(cumple_8h=False).count()
    sin_senal = pernoctaciones_hoy.filter(sin_senal=True).count()

    ultima_carga = CargaTMS.objects.filter(fecha=hoy).order_by('-creado_en').first()

    context = {
        'hoy': hoy,
        'total': total,
        'pendientes': pendientes,
        'confirmados': confirmados,
        'cumple_00h': cumple_00h,
        'no_cumple_00h': no_cumple_00h,
        'cumple_8h': cumple_8h,
        'no_cumple_8h': no_cumple_8h,
        'sin_senal': sin_senal,
        'ultima_carga': ultima_carga,
        'pernoctaciones': pernoctaciones_hoy.order_by('transporte_nombre'),
    }
    return render(request, 'core/dashboard.html', context)


def inicio(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard')
    return render(request, 'index.html')
