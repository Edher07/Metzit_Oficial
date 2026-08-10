from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Usuario:
    id: int
    usuario: str
    password_hash: str
    nombre: str
    direccion: str
    telefono: str
    parcela: str
    rol: str  # "comisariado" | "usuario"
    activo: bool
    fecha_registro: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"], usuario=row["usuario"], password_hash=row["password_hash"],
            nombre=row["nombre"], direccion=row["direccion"], telefono=row["telefono"],
            parcela=row["parcela"], rol=row["rol"], activo=bool(row["activo"]),
            fecha_registro=row["fecha_registro"],
        )


@dataclass
class Turno:
    id: int
    usuario_id: Optional[int]
    usuario_nombre: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    sector: str
    estado: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"], usuario_id=row["usuario_id"],
            usuario_nombre=row["usuario_nombre"] if "usuario_nombre" in row.keys() else "",
            fecha=row["fecha"], hora_inicio=row["hora_inicio"], hora_fin=row["hora_fin"],
            sector=row["sector"], estado=row["estado"],
        )


@dataclass
class Aviso:
    id: int
    titulo: str
    contenido: str
    tipo: str
    alcance: str  # "general" | "personal"
    fecha: str
    hora: str
    autor: str
    activo: bool
    destinatarios: List[str] = field(default_factory=list)  # nombres, solo si alcance == "personal"
    destinatario_ids: List[int] = field(default_factory=list)  # ids, para prellenar el formulario de edición

    @classmethod
    def from_row(cls, row, destinatarios=None, destinatario_ids=None):
        if row is None:
            return None
        return cls(
            id=row["id"], titulo=row["titulo"], contenido=row["contenido"], tipo=row["tipo"],
            alcance=row["alcance"] if "alcance" in row.keys() else "general",
            fecha=row["fecha"], hora=(row["hora"] if "hora" in row.keys() else "") or "",
            autor=row["autor"], activo=bool(row["activo"]),
            destinatarios=destinatarios or [],
            destinatario_ids=destinatario_ids or [],
        )


@dataclass
class Actividad:
    id: int
    tipo: str
    titulo: str
    descripcion: str
    fecha: str
    hora: str
    lugar: str
    multa: Optional[int]
    participantes: List[str]

    @classmethod
    def from_row(cls, row, participantes=None):
        if row is None:
            return None
        return cls(
            id=row["id"], tipo=row["tipo"], titulo=row["titulo"], descripcion=row["descripcion"],
            fecha=row["fecha"], hora=row["hora"], lugar=row["lugar"], multa=row["multa"],
            participantes=participantes or [],
        )


@dataclass
class Multa:
    id: int
    usuario_id: int
    usuario_nombre: str
    concepto: str
    descripcion: str
    monto_total: float
    monto_pagado: float
    estado: str  # "pendiente" | "parcial" | "pagada"
    fecha: str
    actividad_id: Optional[int]
    creado_por: str

    @property
    def saldo(self):
        return round(self.monto_total - self.monto_pagado, 2)

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"], usuario_id=row["usuario_id"],
            usuario_nombre=row["usuario_nombre"] if "usuario_nombre" in row.keys() else "",
            concepto=row["concepto"], descripcion=row["descripcion"],
            monto_total=row["monto_total"], monto_pagado=row["monto_pagado"],
            estado=row["estado"], fecha=row["fecha"], actividad_id=row["actividad_id"],
            creado_por=row["creado_por"],
        )


@dataclass
class PagoMulta:
    id: int
    multa_id: int
    monto: float
    fecha: str
    registrado_por: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"], multa_id=row["multa_id"], monto=row["monto"],
            fecha=row["fecha"], registrado_por=row["registrado_por"],
        )


@dataclass
class Cultivo:
    id: int
    nombre: str
    temporada: str
    frecuencia_riego: str
    consumo_agua: str
    descripcion: str
    accent: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"], nombre=row["nombre"], temporada=row["temporada"],
            frecuencia_riego=row["frecuencia_riego"], consumo_agua=row["consumo_agua"],
            descripcion=row["descripcion"], accent=row["accent"],
        )
