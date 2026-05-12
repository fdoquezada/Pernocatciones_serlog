from django.db import models
from django.contrib.auth.models import User
import uuid


class Transporte(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    email = models.EmailField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Transporte'
        verbose_name_plural = 'Transportes'
        ordering = ['nombre']


class CargaTMS(models.Model):
    """Registro de cada archivo TMS subido"""
    fecha = models.DateField(auto_now_add=True)
    archivo = models.FileField(upload_to='tms/')
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    total_registros = models.IntegerField(default=0)
    total_filtrados = models.IntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carga TMS {self.fecha}"

    class Meta:
        verbose_name = 'Carga TMS'
        verbose_name_plural = 'Cargas TMS'
        ordering = ['-fecha']


class Pernoctacion(models.Model):

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado por Transporte'),
        ('VALIDADO_1', 'Validado Turno Noche'),
        ('VALIDADO_2', 'Validado 8 Horas'),
        ('CERRADO', 'Cerrado'),
    ]

    # Datos del TMS
    carga = models.ForeignKey(CargaTMS, on_delete=models.CASCADE, null=True)
    id_pedido = models.CharField(max_length=50)
    id_viaje = models.CharField(max_length=50)
    cliente = models.CharField(max_length=200)
    transporte = models.ForeignKey(Transporte, on_delete=models.SET_NULL, null=True, blank=True)
    transporte_nombre = models.CharField(max_length=200)  # tal como viene del TMS
    patente = models.CharField(max_length=20)
    patente_secundaria = models.CharField(max_length=20, blank=True)
    conductor = models.CharField(max_length=200)
    fecha_inicio_plan = models.DateTimeField(null=True, blank=True)
    fecha_fin_plan = models.DateField(null=True, blank=True)
    fecha_plan_descarga = models.DateField(null=True, blank=True)
    direccion_descarga = models.CharField(max_length=300, blank=True)
    operacion = models.CharField(max_length=100, blank=True)
    categoria = models.CharField(max_length=100, blank=True)

    # Token para link público del transporte
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    mail_enviado = models.BooleanField(default=False)
    mail_enviado_en = models.DateTimeField(null=True, blank=True)

    # PRIMERA VALIDACIÓN — Transporte responde
    lugar_pernoctacion = models.CharField(max_length=300, blank=True)
    hora_eta = models.TimeField(null=True, blank=True)
    respondido_en = models.DateTimeField(null=True, blank=True)

    # SEGUNDA VALIDACIÓN — Turno noche (llegada antes 00:00)
    hora_llegada_real = models.DateTimeField(null=True, blank=True)
    cumple_00h = models.BooleanField(null=True, blank=True)
    extension_horaria = models.BooleanField(default=False)
    observaciones_primera = models.TextField(blank=True)
    validado_primera_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validaciones_primera'
    )

    # TERCERA VALIDACIÓN — Turno noche (8 horas)
    hora_salida = models.DateTimeField(null=True, blank=True)
    cumple_8h = models.BooleanField(null=True, blank=True)
    horas_totales = models.DurationField(null=True, blank=True)
    observaciones_segunda = models.TextField(blank=True)
    validado_segunda_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validaciones_segunda'
    )

    # Sin señal
    sin_senal = models.BooleanField(default=False)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_registro = models.DateField(auto_now_add=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patente} - {self.conductor} ({self.fecha_registro})"

    def horas_totales_display(self):
        if self.horas_totales:
            total = int(self.horas_totales.total_seconds())
            h = total // 3600
            m = (total % 3600) // 60
            return f"{h}h {m}min"
        return "-"

    class Meta:
        verbose_name = 'Pernoctación'
        verbose_name_plural = 'Pernoctaciones'
        ordering = ['-fecha_registro', 'transporte_nombre']
