import pandas as pd
from datetime import date, timedelta


USUARIOS_PRY = ['YROSALES', 'ACALDERON', 'ERIVERO']
CATEGORIAS_EXCLUIR = ['URGENCIA', 'Urgencia Corta', 'Urgencia Larga', 'MOV. INTERNO']
ESTADOS_MANTENER = ['Activo', 'Inactivo']


def procesar_tms(archivo) -> pd.DataFrame:
    df = pd.read_excel(archivo, dtype=str)
    df.columns = df.columns.str.strip()
    total_original = len(df)

    # FILTRO 1: Operación
    mask_distribucion = df['Operación'] == 'DISTRIBUCION'
    mask_pry = (
        (df['Operación'] == 'PRY TRANSPORTE DE PROYECTOS') &
        (df['Usuario Creador'].isin(USUARIOS_PRY))
    )
    df = df[mask_distribucion | mask_pry].copy()

    # FILTRO 2: Categoría
    df = df[~df['Categoria'].isin(CATEGORIAS_EXCLUIR)].copy()

    # FILTRO 3: Viaje Fecha Inicio Plan <= hoy
    hoy = date.today()
    df['Viaje Fecha Inicio Plan'] = pd.to_datetime(
        df['Viaje Fecha Inicio Plan'], dayfirst=True, errors='coerce'
    )
    df = df[df['Viaje Fecha Inicio Plan'].dt.date <= hoy].copy()

    # FILTRO 4: Viaje Fecha Fin Plan >= mañana
    manana = hoy + timedelta(days=1)
    df['Viaje Fecha Fin Plan'] = pd.to_datetime(
        df['Viaje Fecha Fin Plan'], dayfirst=True, errors='coerce'
    )
    df = df[df['Viaje Fecha Fin Plan'].dt.date >= manana].copy()

    # FILTRO 5: Estado Viaje
    df = df[df['Estado Viaje'].isin(ESTADOS_MANTENER)].copy()

    total_filtrado = len(df)
    df.attrs['total_original'] = total_original
    df.attrs['total_filtrado'] = total_filtrado

    return df


def _fecha_str(valor):
    """Convierte fecha/datetime a string YYYY-MM-DD para sesión JSON."""
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass
    if hasattr(valor, 'strftime'):
        return valor.strftime('%Y-%m-%d')
    return str(valor)


def _datetime_str(valor):
    """Convierte datetime a string para sesión JSON."""
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass
    if hasattr(valor, 'strftime'):
        return valor.strftime('%Y-%m-%d %H:%M:%S')
    return str(valor)


def extraer_campos_pernoctacion(df: pd.DataFrame) -> list[dict]:
    """
    Extrae solo los campos necesarios.
    Todas las fechas se convierten a string para poder guardarlas en sesión JSON.
    """
    registros = []

    for _, row in df.iterrows():
        fecha_fin = row.get('Viaje Fecha Fin Plan')
        fecha_descarga = pd.to_datetime(
            row.get('Fecha Plan Descarga'), dayfirst=True, errors='coerce'
        )

        registros.append({
            'id_pedido':          str(row.get('Id Pedido', '')).strip(),
            'id_viaje':           str(row.get('Id Viaje', '')).strip(),
            'cliente':            str(row.get('Cliente', '')).strip(),
            'transporte_nombre':  str(row.get('Proveedor TTE', '')).strip(),
            'patente':            str(row.get('Patente Principal', '')).strip(),
            'patente_secundaria': str(row.get('Patente Secundaria', '')).strip(),
            'conductor':          str(row.get('Chofer', '')).strip(),
            'fecha_inicio_plan':  _datetime_str(row.get('Viaje Fecha Inicio Plan')),
            'fecha_fin_plan':     _fecha_str(fecha_fin),
            'fecha_plan_descarga':_fecha_str(fecha_descarga),
            'direccion_descarga': str(row.get('Dirección Descarga Pedido', '')).strip(),
            'operacion':          str(row.get('Operación', '')).strip(),
            'categoria':          str(row.get('Categoria', '')).strip(),
        })

    return registros
