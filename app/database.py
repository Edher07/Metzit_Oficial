 vez que se levanta el servidor.
"""
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario         TEXT NOT NULL UNIQUE,   -- nombre de acceso (login)
    password_hash   TEXT NOT NULL,
    nombre          TEXT NOT NULL,
    direccion       TEXT,
    telefono        TEXT,
    parcela         TEXT,
    rol             TEXT NOT NULL CHECK (rol IN ('comisariado', 'usuario')),
    activo          INTEGER NOT NULL DEFAULT 1,
    fecha_registro  TEXT
);

-- Nota: los usuarios ya no se eliminan físicamente (solo se activan/desactivan),
-- por eso turnos, multas y demás registros siempre conservan una referencia
-- válida a un usuario real y nunca deben mostrar "(usuario eliminado)".
CREATE TABLE IF NOT EXISTS turnos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
    fecha           TEXT NOT NULL,
    hora_inicio     TEXT NOT NULL,
    hora_fin        TEXT NOT NULL,
    sector          TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'programado'
                    CHECK (estado IN ('programado','en_curso','completado','cancelado'))
);

-- alcance='general': visible para toda la comunidad.
-- alcance='personal': visible solo para el comisariado y los usuarios listados
-- en aviso_destinatarios.
CREATE TABLE IF NOT EXISTS avisos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo          TEXT NOT NULL,
    contenido       TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'informativo'
                    CHECK (tipo IN ('informativo','urgente','mantenimiento','incidencia')),
    alcance         TEXT NOT NULL DEFAULT 'general' CHECK (alcance IN ('general','personal')),
    fecha           TEXT NOT NULL,
    hora            TEXT NOT NULL DEFAULT '',
    autor           TEXT NOT NULL,
    activo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS aviso_destinatarios (
    aviso_id        INTEGER NOT NULL REFERENCES avisos(id) ON DELETE CASCADE,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
    PRIMARY KEY (aviso_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS actividades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL DEFAULT 'faena' CHECK (tipo IN ('faena','junta')),
    titulo          TEXT NOT NULL,
    descripcion     TEXT,
    fecha           TEXT NOT NULL,
    hora            TEXT NOT NULL,
    lugar           TEXT,
    multa           INTEGER
);

CREATE TABLE IF NOT EXISTS actividad_participantes (
    actividad_id    INTEGER NOT NULL REFERENCES actividades(id) ON DELETE CASCADE,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    PRIMARY KEY (actividad_id, usuario_id)
);

-- Multas: solo el comisariado ve todas; un usuario normal solo ve las suyas.
-- El saldo pendiente (monto_total - monto_pagado) se actualiza mediante abonos
-- registrados en multa_pagos, y el estado se recalcula automáticamente.
CREATE TABLE IF NOT EXISTS multas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
    concepto        TEXT NOT NULL,
    descripcion     TEXT,
    monto_total     REAL NOT NULL,
    monto_pagado    REAL NOT NULL DEFAULT 0,
    estado          TEXT NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente','parcial','pagada')),
    fecha           TEXT NOT NULL,
    actividad_id    INTEGER REFERENCES actividades(id) ON DELETE SET NULL,
    creado_por      TEXT
);

CREATE TABLE IF NOT EXISTS multa_pagos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    multa_id        INTEGER NOT NULL REFERENCES multas(id) ON DELETE CASCADE,
    monto           REAL NOT NULL,
    fecha           TEXT NOT NULL,
    registrado_por  TEXT
);

CREATE TABLE IF NOT EXISTS cultivos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    temporada       TEXT,
    frecuencia_riego TEXT,
    consumo_agua    TEXT,
    descripcion     TEXT,
    accent          TEXT NOT NULL DEFAULT '#16A34A'
);


CREATE TABLE IF NOT EXISTS historial_actividades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    tipo_accion TEXT NOT NULL,        -- 'crear_turno', 'cancelar_turno', 'editar_turno', 'login', etc.
    modulo TEXT NOT NULL,             -- 'turnos', 'avisos', 'usuarios', etc.
    descripcion TEXT,                 -- texto legible: "Canceló turno de riego Sector Oriente"
    entidad_id INTEGER,               -- id del turno/aviso/etc afectado (opcional)
    fecha_hora TEXT NOT NULL,         -- ISO 8601: '2026-08-06T12:40:04'
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def init_db(app):
    """Crea las tablas (si no existen) y siembra los datos iniciales una sola vez."""
    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE_PATH"])
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA_SQL)
        db.commit()
        _migrar_si_necesario(db)
        _seed_if_empty(db)
        db.close()


def _migrar_si_necesario(db):
    """Agrega columnas nuevas a bases de datos creadas con una versión
    anterior del esquema, sin perder los datos ya existentes."""
    columnas_avisos = {r["name"] for r in db.execute("PRAGMA table_info(avisos)")}
    if "hora" not in columnas_avisos:
        db.execute("ALTER TABLE avisos ADD COLUMN hora TEXT NOT NULL DEFAULT ''")
        db.commit()


def _seed_if_empty(db):
    # Solo se siembra la cuenta del comisariado (para poder entrar la primera
    # vez) y el catálogo agrícola informativo. Ya no se crean usuarios,
    # turnos, avisos, faenas/reuniones ni multas de prueba: esos datos ahora
    # solo existen cuando alguien realmente los da de alta desde la app
    # (registro propio de usuarios, o altas del comisariado).
    if db.execute("SELECT COUNT(*) AS c FROM usuarios").fetchone()["c"] == 0:
        _seed_usuarios(db)
    if db.execute("SELECT COUNT(*) AS c FROM cultivos").fetchone()["c"] == 0:
        _seed_cultivos(db)
    db.commit()


def _seed_usuarios(db):
    # Única cuenta sembrada: el comisariado (administrador). El resto de las
    # cuentas se crean desde la app, ya sea por autorregistro público
    # ("¿No tienes cuenta? Regístrate") o dadas de alta por el comisariado
    # desde el módulo de Usuarios.
    usuarios = [
        # usuario(login), password demo, nombre, direccion, telefono, parcela, rol, activo, fecha_registro
        ("comisariado", "1234", "Manuel Ramiro Soto", "Calle Principal s/n", "775-101-2030", "Administrador", "comisariado", 1, "1 ene. 2026"),
    ]
    for u, pw, nombre, direccion, telefono, parcela, rol, activo, fecha in usuarios:
        db.execute(
            """INSERT INTO usuarios (usuario, password_hash, nombre, direccion, telefono, parcela, rol, activo, fecha_registro)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (u, generate_password_hash(pw), nombre, direccion, telefono, parcela, rol, activo, fecha),
        )


def _seed_cultivos(db):
    cultivos = [
        ("Maíz (Milpa)", "Mayo – Octubre", "Cada 7 días", "5–8 L/m²",
         "Cultivo principal de la comunidad. Requiere riego regular en germinación y floración. Reducir en periodo de lluvias.", "#CA8A04"),
        ("Frijol", "Junio – Noviembre", "Cada 5 días", "4–6 L/m²",
         "Se siembra intercalado con el maíz en la milpa. Sensible al exceso de humedad. Reducir riego en la etapa de llenado del grano.", "#EA580C"),
        ("Nopal", "Todo el año", "Cada 14 días", "2–3 L/m²",
         "Muy resistente a la sequía. Riego mínimo en temporada de lluvias. Ideal para sectores con escasa disponibilidad hídrica.", "#16A34A"),
        ("Chile Serrano", "Marzo – Agosto", "Cada 4 días", "5–7 L/m²",
         "Requiere riego frecuente y constante. Muy sensible al estrés hídrico en floración. Evitar encharcamiento.", "#DC2626"),
        ("Quelite / Verdolaga", "Junio – Septiembre", "Cada 6 días", "3–4 L/m²",
         "Planta comestible silvestre de alto valor nutritivo. Poco exigente en riego. Crece espontáneamente en las parcelas.", "#0D9488"),
        ("Calabaza", "Abril – Septiembre", "Cada 6 días", "5–7 L/m²",
         "Parte del sistema milpa junto al maíz y el frijol. Cubre el suelo reduciendo la evaporación. Riego moderado y constante.", "#D97706"),
    ]
    for nombre, temporada, freq, consumo, desc, accent in cultivos:
        db.execute(
            "INSERT INTO cultivos (nombre, temporada, frecuencia_riego, consumo_agua, descripcion, accent) VALUES (?,?,?,?,?,?)",
            (nombre, temporada, freq, consumo, desc, accent),
        )
