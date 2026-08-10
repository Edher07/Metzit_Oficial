from database import get_db
from modelos import Usuario, Turno, Aviso, Actividad, Multa, PagoMulta, Cultivo
from constantes import hoy as hoy_local, ahora as ahora_local


# ---------------------------------------------------------------- usuarios --

def usuario_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return Usuario.from_row(row)


def usuario_por_login(usuario):
    row = get_db().execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
    return Usuario.from_row(row)


def todos_los_usuarios():
    rows = get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [Usuario.from_row(r) for r in rows]


def usuarios_multables():
    """Cuentas con rol 'usuario': las multas son solo para usuarios de la
    comunidad, nunca para la cuenta del comisariado."""
    rows = get_db().execute("SELECT * FROM usuarios WHERE rol = 'usuario' ORDER BY id").fetchall()
    return [Usuario.from_row(r) for r in rows]


def usuarios_activos_count():
    return get_db().execute("SELECT COUNT(*) c FROM usuarios WHERE activo = 1").fetchone()["c"]


def crear_usuario(usuario, password_hash, nombre, direccion, telefono, parcela, rol, fecha_registro):
    db = get_db()
    cur = db.execute(
        """INSERT INTO usuarios (usuario, password_hash, nombre, direccion, telefono, parcela, rol, activo, fecha_registro)
           VALUES (?,?,?,?,?,?,?,1,?)""",
        (usuario, password_hash, nombre, direccion, telefono, parcela, rol, fecha_registro),
    )
    db.commit()
    return usuario_por_id(cur.lastrowid)


def editar_usuario(usuario_id, nombre, direccion, telefono, parcela, rol, password_hash=None):
    db = get_db()
    if password_hash:
        db.execute(
            """UPDATE usuarios SET nombre = ?, direccion = ?, telefono = ?, parcela = ?, rol = ?, password_hash = ?
               WHERE id = ?""",
            (nombre, direccion, telefono, parcela, rol, password_hash, usuario_id),
        )
    else:
        db.execute(
            "UPDATE usuarios SET nombre = ?, direccion = ?, telefono = ?, parcela = ?, rol = ? WHERE id = ?",
            (nombre, direccion, telefono, parcela, rol, usuario_id),
        )
    db.commit()
    return usuario_por_id(usuario_id)


def alternar_usuario_activo(usuario_id):
    db = get_db()
    db.execute("UPDATE usuarios SET activo = 1 - activo WHERE id = ?", (usuario_id,))
    db.commit()


# Nota: los usuarios ya no se eliminan físicamente (ver database.py) — solo se
# activan/desactivan — para que turnos, multas y avisos personales conserven
# siempre una referencia válida y nunca muestren "(usuario eliminado)".


# ------------------------------------------------------------------ turnos --

_TURNOS_SELECT = """
    SELECT t.*, u.nombre AS usuario_nombre
    FROM turnos t JOIN usuarios u ON u.id = t.usuario_id
"""


def _sincronizar_estados_turnos(db):
    """Actualiza automáticamente el estado de los turnos según la fecha/hora
    real (zona horaria de la comunidad), para que el horario mostrado siempre
    vaya acorde al reloj del sistema:
      - programado -> en_curso   cuando ya inició y no ha terminado
      - programado/en_curso -> completado   cuando ya terminó
    Los turnos cancelados nunca se tocan (siempre es una acción manual)."""
    hoy = hoy_local().isoformat()
    ahora = ahora_local().strftime("%H:%M")
    db.execute(
        """UPDATE turnos SET estado = 'en_curso'
           WHERE estado = 'programado' AND fecha = ? AND hora_inicio <= ? AND hora_fin > ?""",
        (hoy, ahora, ahora),
    )
    db.execute(
        """UPDATE turnos SET estado = 'completado'
           WHERE estado IN ('programado', 'en_curso')
             AND (fecha < ? OR (fecha = ? AND hora_fin <= ?))""",
        (hoy, hoy, ahora),
    )
    db.commit()


def todos_los_turnos():
    db = get_db()
    _sincronizar_estados_turnos(db)
    rows = db.execute(_TURNOS_SELECT + " ORDER BY t.fecha, t.hora_inicio").fetchall()
    return [Turno.from_row(r) for r in rows]


def turnos_por_estado(estado):
    db = get_db()
    _sincronizar_estados_turnos(db)
    if estado == "todos":
        rows = db.execute(_TURNOS_SELECT + " ORDER BY t.fecha, t.hora_inicio").fetchall()
        return [Turno.from_row(r) for r in rows]
    rows = db.execute(_TURNOS_SELECT + " WHERE t.estado = ? ORDER BY t.fecha, t.hora_inicio", (estado,)).fetchall()
    return [Turno.from_row(r) for r in rows]


def turno_por_id(turno_id):
    row = get_db().execute(_TURNOS_SELECT + " WHERE t.id = ?", (turno_id,)).fetchone()
    return Turno.from_row(row)


def turno_en_curso():
    db = get_db()
    _sincronizar_estados_turnos(db)
    row = db.execute(_TURNOS_SELECT + " WHERE t.estado = 'en_curso' LIMIT 1").fetchone()
    return Turno.from_row(row)


def turnos_count_semana(fecha_inicio, fecha_fin):
    row = get_db().execute(
        "SELECT COUNT(*) c FROM turnos WHERE fecha BETWEEN ? AND ?", (fecha_inicio, fecha_fin)).fetchone()
    return row["c"]


def crear_turno(usuario_id, fecha, hora_inicio, hora_fin, sector):
    db = get_db()
    cur = db.execute(
        "INSERT INTO turnos (usuario_id, fecha, hora_inicio, hora_fin, sector, estado) VALUES (?,?,?,?,?,'programado')",
        (usuario_id, fecha, hora_inicio, hora_fin, sector),
    )
    db.commit()
    return turno_por_id(cur.lastrowid)


def existe_turno_traslapado(fecha, hora_inicio, hora_fin, sector, excluir_turno_id=None):
    """True si ya hay un turno activo (no cancelado) en el mismo sector y fecha
    cuyo horario se traslapa con [hora_inicio, hora_fin)."""
    query = """SELECT 1 FROM turnos
               WHERE fecha = ? AND sector = ? AND estado != 'cancelado'
                 AND hora_inicio < ? AND hora_fin > ?"""
    params = [fecha, sector, hora_fin, hora_inicio]
    if excluir_turno_id is not None:
        query += " AND id != ?"
        params.append(excluir_turno_id)
    row = get_db().execute(query + " LIMIT 1", params).fetchone()
    return row is not None


def alternar_turno_cancelado(turno_id):
    db = get_db()
    t = turno_por_id(turno_id)
    if not t:
        return
    nuevo_estado = "programado" if t.estado == "cancelado" else "cancelado"
    db.execute("UPDATE turnos SET estado = ? WHERE id = ?", (nuevo_estado, turno_id))
    db.commit()


def editar_turno(turno_id, usuario_id, fecha, hora_inicio, hora_fin, sector, estado):
    db = get_db()
    db.execute(
        """UPDATE turnos SET usuario_id = ?, fecha = ?, hora_inicio = ?, hora_fin = ?,
                              sector = ?, estado = ? WHERE id = ?""",
        (usuario_id, fecha, hora_inicio, hora_fin, sector, estado, turno_id),
    )
    db.commit()
    return turno_por_id(turno_id)


# ------------------------------------------------------------------ avisos --

def _destinatarios_de_aviso(db, aviso_id):
    rows = db.execute(
        """SELECT u.nombre FROM aviso_destinatarios ad
           JOIN usuarios u ON u.id = ad.usuario_id WHERE ad.aviso_id = ?""",
        (aviso_id,)).fetchall()
    return [r["nombre"] for r in rows]


def _destinatario_ids_de_aviso(db, aviso_id):
    rows = db.execute(
        "SELECT usuario_id FROM aviso_destinatarios WHERE aviso_id = ?",
        (aviso_id,)).fetchall()
    return [r["usuario_id"] for r in rows]


def todos_los_avisos():
    """Uso exclusivo del comisariado: ve todos los avisos, generales y personales."""
    db = get_db()
    rows = db.execute("SELECT * FROM avisos ORDER BY id DESC").fetchall()
    return [Aviso.from_row(r, _destinatarios_de_aviso(db, r["id"]), _destinatario_ids_de_aviso(db, r["id"]))
            for r in rows]


def aviso_por_id(aviso_id):
    db = get_db()
    row = db.execute("SELECT * FROM avisos WHERE id = ?", (aviso_id,)).fetchone()
    if row is None:
        return None
    return Aviso.from_row(row, _destinatarios_de_aviso(db, aviso_id), _destinatario_ids_de_aviso(db, aviso_id))


def avisos_visibles_para(usuario_id):
    """Avisos generales + avisos personales dirigidos a este usuario."""
    db = get_db()
    rows = db.execute(
        """SELECT DISTINCT a.* FROM avisos a
           LEFT JOIN aviso_destinatarios ad ON ad.aviso_id = a.id
           WHERE a.alcance = 'general' OR ad.usuario_id = ?
           ORDER BY a.id DESC""",
        (usuario_id,)).fetchall()
    return [Aviso.from_row(r, _destinatarios_de_aviso(db, r["id"])) for r in rows]


def avisos_activos_count():
    return get_db().execute("SELECT COUNT(*) c FROM avisos WHERE activo = 1").fetchone()["c"]


def crear_aviso(titulo, contenido, tipo, alcance, autor, fecha, hora, destinatario_ids=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO avisos (titulo, contenido, tipo, alcance, fecha, hora, autor, activo) VALUES (?,?,?,?,?,?,?,1)",
        (titulo, contenido, tipo, alcance, fecha, hora, autor),
    )
    aviso_id = cur.lastrowid
    if alcance == "personal":
        for usuario_id in (destinatario_ids or []):
            db.execute("INSERT INTO aviso_destinatarios (aviso_id, usuario_id) VALUES (?,?)",
                       (aviso_id, usuario_id))
    db.commit()
    return aviso_id


def editar_aviso(aviso_id, titulo, contenido, tipo, alcance, destinatario_ids=None):
    db = get_db()
    db.execute(
        "UPDATE avisos SET titulo = ?, contenido = ?, tipo = ?, alcance = ? WHERE id = ?",
        (titulo, contenido, tipo, alcance, aviso_id),
    )
    # Siempre se reemplazan los destinatarios: si el alcance cambió a
    # 'general' no debe quedar ningún destinatario personal residual.
    db.execute("DELETE FROM aviso_destinatarios WHERE aviso_id = ?", (aviso_id,))
    if alcance == "personal":
        for usuario_id in (destinatario_ids or []):
            db.execute("INSERT INTO aviso_destinatarios (aviso_id, usuario_id) VALUES (?,?)",
                       (aviso_id, usuario_id))
    db.commit()


def eliminar_aviso(aviso_id):
    db = get_db()
    db.execute("DELETE FROM avisos WHERE id = ?", (aviso_id,))
    db.commit()


# -------------------------------------------------------------- actividades --

def _participantes_de(db, actividad_id):
    rows = db.execute(
        """SELECT u.nombre FROM actividad_participantes ap
           JOIN usuarios u ON u.id = ap.usuario_id WHERE ap.actividad_id = ?""",
        (actividad_id,)).fetchall()
    return [r["nombre"] for r in rows]


def todas_las_actividades():
    db = get_db()
    rows = db.execute("SELECT * FROM actividades ORDER BY id DESC").fetchall()
    return [Actividad.from_row(r, _participantes_de(db, r["id"])) for r in rows]


def actividad_por_id(actividad_id):
    db = get_db()
    row = db.execute("SELECT * FROM actividades WHERE id = ?", (actividad_id,)).fetchone()
    return Actividad.from_row(row, _participantes_de(db, actividad_id)) if row else None


def proxima_actividad():
    from constantes import hoy as hoy_local
    hoy = hoy_local().isoformat()
    db = get_db()
    row = db.execute(
        "SELECT * FROM actividades WHERE fecha >= ? ORDER BY fecha, hora LIMIT 1", (hoy,)
    ).fetchone()
    return Actividad.from_row(row, _participantes_de(db, row["id"])) if row else None


def crear_actividad(tipo, titulo, descripcion, fecha, hora, lugar, multa):
    db = get_db()
    cur = db.execute(
        "INSERT INTO actividades (tipo, titulo, descripcion, fecha, hora, lugar, multa) VALUES (?,?,?,?,?,?,?)",
        (tipo, titulo, descripcion, fecha, hora, lugar, multa),
    )
    db.commit()
    return cur.lastrowid


def editar_actividad(actividad_id, tipo, titulo, descripcion, fecha, hora, lugar, multa):
    db = get_db()
    db.execute(
        """UPDATE actividades SET tipo = ?, titulo = ?, descripcion = ?, fecha = ?,
                                   hora = ?, lugar = ?, multa = ? WHERE id = ?""",
        (tipo, titulo, descripcion, fecha, hora, lugar, multa, actividad_id),
    )
    db.commit()


def alternar_asistencia(actividad_id, usuario_id):
    db = get_db()
    ya = db.execute(
        "SELECT 1 FROM actividad_participantes WHERE actividad_id = ? AND usuario_id = ?",
        (actividad_id, usuario_id)).fetchone()
    if ya:
        db.execute("DELETE FROM actividad_participantes WHERE actividad_id = ? AND usuario_id = ?",
                    (actividad_id, usuario_id))
    else:
        db.execute("INSERT INTO actividad_participantes (actividad_id, usuario_id) VALUES (?,?)",
                    (actividad_id, usuario_id))
    db.commit()


# ------------------------------------------------------------------ multas --

_MULTAS_SELECT = """
    SELECT m.*, u.nombre AS usuario_nombre
    FROM multas m JOIN usuarios u ON u.id = m.usuario_id
"""


def todas_las_multas():
    """Uso exclusivo del comisariado."""
    rows = get_db().execute(_MULTAS_SELECT + " ORDER BY m.id DESC").fetchall()
    return [Multa.from_row(r) for r in rows]


def multas_de_usuario(usuario_id):
    rows = get_db().execute(
        _MULTAS_SELECT + " WHERE m.usuario_id = ? ORDER BY m.id DESC", (usuario_id,)).fetchall()
    return [Multa.from_row(r) for r in rows]


def multa_por_id(multa_id):
    row = get_db().execute(_MULTAS_SELECT + " WHERE m.id = ?", (multa_id,)).fetchone()
    return Multa.from_row(row)


def pagos_de_multa(multa_id):
    rows = get_db().execute(
        "SELECT * FROM multa_pagos WHERE multa_id = ? ORDER BY id DESC", (multa_id,)).fetchall()
    return [PagoMulta.from_row(r) for r in rows]


def crear_multa(usuario_id, concepto, descripcion, monto_total, fecha, actividad_id, creado_por):
    db = get_db()
    cur = db.execute(
        """INSERT INTO multas (usuario_id, concepto, descripcion, monto_total, monto_pagado, estado, fecha, actividad_id, creado_por)
           VALUES (?,?,?,?,0,'pendiente',?,?,?)""",
        (usuario_id, concepto, descripcion, monto_total, fecha, actividad_id, creado_por),
    )
    db.commit()
    return multa_por_id(cur.lastrowid)


def editar_multa(multa_id, concepto, descripcion, monto_total, fecha):
    db = get_db()
    db.execute(
        "UPDATE multas SET concepto = ?, descripcion = ?, monto_total = ?, fecha = ? WHERE id = ?",
        (concepto, descripcion, monto_total, fecha, multa_id),
    )
    _recalcular_estado_multa(db, multa_id)
    db.commit()
    return multa_por_id(multa_id)


def eliminar_multa(multa_id):
    db = get_db()
    db.execute("DELETE FROM multa_pagos WHERE multa_id = ?", (multa_id,))
    db.execute("DELETE FROM multas WHERE id = ?", (multa_id,))
    db.commit()


def _recalcular_estado_multa(db, multa_id):
    row = db.execute("SELECT monto_total, monto_pagado FROM multas WHERE id = ?", (multa_id,)).fetchone()
    if row is None:
        return
    total, pagado = row["monto_total"], row["monto_pagado"]
    if pagado <= 0:
        estado = "pendiente"
    elif pagado >= total:
        estado = "pagada"
    else:
        estado = "parcial"
    db.execute("UPDATE multas SET estado = ? WHERE id = ?", (estado, multa_id))


def registrar_pago_multa(multa_id, monto, fecha, registrado_por):
    db = get_db()
    db.execute(
        "INSERT INTO multa_pagos (multa_id, monto, fecha, registrado_por) VALUES (?,?,?,?)",
        (multa_id, monto, fecha, registrado_por),
    )
    db.execute("UPDATE multas SET monto_pagado = monto_pagado + ? WHERE id = ?", (monto, multa_id))
    _recalcular_estado_multa(db, multa_id)
    db.commit()
    return multa_por_id(multa_id)


def multas_pendientes_count_de_usuario(usuario_id):
    row = get_db().execute(
        "SELECT COUNT(*) c FROM multas WHERE usuario_id = ? AND estado != 'pagada'", (usuario_id,)
    ).fetchone()
    return row["c"]


# ----------------------------------------------------------------- cultivos --

def todos_los_cultivos():
    rows = get_db().execute("SELECT * FROM cultivos ORDER BY id").fetchall()
    return [Cultivo.from_row(r) for r in rows]


def crear_cultivo(nombre, temporada, frecuencia_riego, consumo_agua, descripcion, accent):
    db = get_db()
    db.execute(
        """INSERT INTO cultivos (nombre, temporada, frecuencia_riego, consumo_agua, descripcion, accent)
           VALUES (?,?,?,?,?,?)""",
        (nombre, temporada, frecuencia_riego, consumo_agua, descripcion, accent),
    )
    db.commit()


def eliminar_cultivo(cultivo_id):
    db = get_db()
    db.execute("DELETE FROM cultivos WHERE id = ?", (cultivo_id,))
    db.commit()
