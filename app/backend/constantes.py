

from datetime import datetime
from zoneinfo import ZoneInfo

# Todo el pueblo opera en un solo huso horario. Se fija explícitamente en vez
# de usar la hora del servidor (que en hosting/Codespaces suele estar en UTC)
# para que "hoy"/"ahora" siempre coincidan con la hora real de la comunidad,
# sin importar dónde esté desplegada la app.
ZONA_HORARIA = ZoneInfo("America/Mexico_City")


def ahora():
    """Fecha y hora actuales en la zona horaria de la comunidad."""
    return datetime.now(ZONA_HORARIA)


def hoy():
    """Fecha actual (date) en la zona horaria de la comunidad."""
    return ahora().date()


COLORES = {
    "background": "#F4EFE6", "foreground": "#1C1209",
    "card": "#FAF7F0", "primary": "#2B5F6E", "primary_fg": "#FFFFFF",
    "secondary": "#4B7840", "muted": "#E5DDD0", "muted_fg": "#7A6554",
    "accent": "#B5582A", "accent_fg": "#FFFFFF",
    "destructive": "#C0392B", "border": "rgba(28,18,9,0.1)",
    "sidebar": "#152E39", "sidebar_2": "#1E3A45",
    "sidebar_fg": "#E8F4F8", "sidebar_primary": "#4BB5CC",
}

FONT_BODY = "'Nunito Sans', sans-serif"
FONT_HEADING = "'Lora', serif"

NAV_ITEMS = [
    {"id": "dashboard", "label": "Inicio", "icon": "layout-dashboard", "endpoint": "dashboard.ver", "admin_only": False},
    {"id": "turnos", "label": "Turnos de riego", "icon": "droplets", "endpoint": "turnos.listar", "admin_only": False},
    {"id": "avisos", "label": "Avisos comunitarios", "icon": "megaphone", "endpoint": "avisos.listar", "admin_only": False},
    {"id": "actividades", "label": "Faenas y reuniones", "icon": "calendar", "endpoint": "actividades.listar", "admin_only": False},
    {"id": "multas", "label": "Multas", "icon": "wallet", "endpoint": "multas.listar", "admin_only": False},
    {"id": "agricola", "label": "Información agrícola", "icon": "leaf", "endpoint": "agricola.listar", "admin_only": False},
    {"id": "usuarios", "label": "Usuarios", "icon": "users", "endpoint": "usuarios.listar", "admin_only": True},
]

SECTORES = ["Sector Norte", "Sector Sur", "Sector Oriente", "Sector Poniente", "Sector Centro"]

ESTADOS_TURNO = {
    "programado": {"cls": "bg-blue-100 text-blue-700 border-blue-200", "label": "Programado"},
    "en_curso": {"cls": "bg-green-100 text-green-700 border-green-200", "label": "En curso"},
    "completado": {"cls": "bg-gray-100 text-gray-600 border-gray-200", "label": "Completado"},
    "cancelado": {"cls": "bg-red-100 text-red-600 border-red-200", "label": "Cancelado"},
}

TIPOS_AVISO = {
    "informativo": {"cls": "bg-blue-100 text-blue-700 border-blue-200", "label": "Informativo", "icon": "info"},
    "urgente": {"cls": "bg-red-100 text-red-700 border-red-200", "label": "Urgente", "icon": "alert-circle"},
    "mantenimiento": {"cls": "bg-amber-100 text-amber-700 border-amber-200", "label": "Mantenimiento", "icon": "info"},
    "incidencia": {"cls": "bg-orange-100 text-orange-700 border-orange-200", "label": "Incidencia", "icon": "alert-triangle"},
}

ESTADOS_MULTA = {
    "pendiente": {"cls": "bg-red-100 text-red-700 border-red-200", "label": "Pendiente"},
    "parcial": {"cls": "bg-amber-100 text-amber-700 border-amber-200", "label": "Abono parcial"},
    "pagada": {"cls": "bg-green-100 text-green-700 border-green-200", "label": "Pagada"},
}

ALCANCES_AVISO = {
    "general": {"cls": "bg-blue-100 text-blue-700 border-blue-200", "label": "General"},
    "personal": {"cls": "bg-purple-100 text-purple-700 border-purple-200", "label": "Personal"},
}

ACCENT_OPTIONS = [
    {"label": "Amarillo", "value": "#CA8A04", "badge": "bg-yellow-100 text-yellow-800 border-yellow-200"},
    {"label": "Naranja", "value": "#EA580C", "badge": "bg-orange-100 text-orange-800 border-orange-200"},
    {"label": "Verde", "value": "#16A34A", "badge": "bg-green-100 text-green-800 border-green-200"},
    {"label": "Rojo", "value": "#DC2626", "badge": "bg-red-100 text-red-800 border-red-200"},
    {"label": "Teal", "value": "#0D9488", "badge": "bg-teal-100 text-teal-800 border-teal-200"},
    {"label": "Azul", "value": "#2563EB", "badge": "bg-blue-100 text-blue-800 border-blue-200"},
    {"label": "Morado", "value": "#7C3AED", "badge": "bg-purple-100 text-purple-800 border-purple-200"},
    {"label": "Rosa", "value": "#DB2777", "badge": "bg-pink-100 text-pink-800 border-pink-200"},
]

ACCENT_TO_BADGE = {opt["value"]: opt["badge"] for opt in ACCENT_OPTIONS}

MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTO = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def fmt_fecha(fecha_iso):
    """'2026-07-15' -> '15 julio 2026'"""
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} {MESES_LARGO[int(m) - 1]} {y}"


def mes_corto(fecha_iso):
    return MESES_CORTO[int(fecha_iso.split("-")[1]) - 1]


def dia_num(fecha_iso):
    return int(fecha_iso.split("-")[2])
