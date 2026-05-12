from django.contrib import admin
from .models import Transporte, CargaTMS, Pernoctacion


@admin.register(Transporte)
class TransporteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'activo']
    search_fields = ['nombre', 'email']
    list_filter = ['activo']


@admin.register(CargaTMS)
class CargaTMSAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'subido_por', 'total_registros', 'total_filtrados', 'creado_en']
    list_filter = ['fecha']


@admin.register(Pernoctacion)
class PernoctacionAdmin(admin.ModelAdmin):
    list_display = ['fecha_registro', 'patente', 'conductor', 'transporte_nombre',
                    'cliente', 'lugar_pernoctacion', 'cumple_00h', 'cumple_8h', 'estado']
    list_filter = ['fecha_registro', 'estado', 'cumple_00h', 'cumple_8h', 'sin_senal']
    search_fields = ['patente', 'conductor', 'transporte_nombre', 'cliente']
    readonly_fields = ['token', 'creado_en', 'actualizado_en']
