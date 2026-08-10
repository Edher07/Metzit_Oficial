from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

import datos
from constantes import fmt_fecha, mes_corto, dia_num, hoy as hoy_local, ahora as ahora_local


def _validar_fecha_no_pasada(fecha):
    try:
        fecha_val = date.fromisoformat(fecha)
    except (TypeError, ValueError):
        return "La fecha ingresada no es válida."
    if fecha_val < hoy_local():
        return "No se puede seleccionar una fecha anterior a hoy."
    return None


def _validar_hora_no_pasada(fecha, hora_inicio):
    """Si el turno es para hoy, la hora de inicio no puede ser anterior a la
    hora actual."""
    try:
        fecha_val = date.fromisoformat(fecha)
    except (TypeError, ValueError):
        return None  # la fecha ya se valida aparte
    if fecha_val == hoy_local() and hora_inicio < ahora_local().strftime("%H:%M"):
        return "No se puede seleccionar una hora anterior a la hora actual."
    return None


# -------------------------------------------------------------------- auth --

def autenticar(usuario, password):
    """Devuelve el Usuario si las credenciales son válidas y la cuenta está activa."""
    u = datos.usuario_por_login(usuario.strip())
    if u is None:
        return None, "Usuario o contraseña incorrectos."
    if not u.activo:
        return None, "Esta cuenta ha sido desactivada. Contacta al comisariado."
    if not check_password_hash(u.password_hash, password):
        return None, "Usuario o contraseña incorrectos."
    return u, None


def registrar_usuario_por_comisariado(usuario, password, nombre, direccion, telefono, parcela, rol):
    """Único punto de alta de cuentas: lo realiza el comisariado desde el
    módulo de Usuarios. No existe autorregistro público."""
    usuario = (usuario or "").strip()
    nombre = (nombre or "").strip()
    if not usuario or not password or not nombre:
        return None, "Completa los campos obligatorios."
    if datos.usuario_por_login(usuario) is not None:
        return None, "Ese nombre de usuario ya está en uso."
    if len(password) < 4:
        return None, "La contraseña debe tener al menos 4 caracteres."
    if rol not in ("usuario", "comisariado"):
        rol = "usuario"
    nuevo = datos.crear_usuario(
        usuario=usuario,
        password_hash=generate_password_hash(password),
        nombre=nombre,
        direccion=(direccion or "").strip(),
        telefono=(telefono or "").strip(),
        parcela=(parcela or "").strip(),
        rol=rol,
        fecha_registro=hoy_local().isoformat(),
    )
    return nuevo, None


def editar_usuario(usuario_id, nombre, direccion, telefono, parcela, rol, password=None):
    """Edición de una cuenta por el comisariado. La contraseña solo se
    actualiza si se proporciona una nueva (de lo contrario se conserva la
    actual)."""
    nombre = (nombre or "").strip()
    if not nombre:
        return None, "El nombre es obligatorio."
    if rol not in ("usuario", "comisariado"):
        rol = "usuario"
    if password:
        if len(password) < 4:
            return None, "La contraseña debe tener al menos 4 caracteres."
        password_hash = generate_password_hash(password)
    else:
        password_hash = None
    actualizado = datos.editar_usuario(
        usuario_id=usuario_id,
        nombre=nombre,
        direccion=(direccion or "").strip(),
        telefono=(telefono or "").strip(),
        parcela=(parcela or "").strip(),
        rol=rol,
        password_hash=password_hash,
    )
    return actualizado, None


# --------------------------------------------------------------- dashboard --

def resumen_dashboard(usuario_actual=None):
    hoy = hoy_local()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    resumen = {
        "usuarios_activos": datos.usuarios_activos_count(),
        "turnos_semana": datos.turnos_count_semana(inicio_semana.isoformat(), fin_semana.isoformat()),
        "avisos_activos": datos.avisos_activos_count(),
        "turno_en_curso": datos.turno_en_curso(),
        "proxima_actividad": datos.proxima_actividad(),
    }
    if usuario_actual is not None:
        avisos_visibles = datos.avisos_visibles_para(usuario_actual.id)
        resumen["avisos_recientes"] = avisos_visibles[:3]
        resumen["multas_pendientes"] = datos.multas_pendientes_count_de_usuario(usuario_actual.id)
    else:
        resumen["avisos_recientes"] = datos.todos_los_avisos()[:3]
        resumen["multas_pendientes"] = 0
    return resumen


# ------------------------------------------------------------------ turnos --

def listar_turnos(filtro_estado="todos"):
    return datos.turnos_por_estado(filtro_estado)


def crear_turno(usuario_id, fecha, hora_inicio, hora_fin, sector):
    if not (usuario_id and fecha and hora_inicio and hora_fin and sector):
        return None, "Completa todos los campos del turno."
    error_fecha = _validar_fecha_no_pasada(fecha)
    if error_fecha:
        return None, error_fecha
    error_hora = _validar_hora_no_pasada(fecha, hora_inicio)
    if error_hora:
        return None, error_hora
    if hora_fin <= hora_inicio:
        return None, "La hora de fin debe ser posterior a la hora de inicio."
    if datos.existe_turno_traslapado(fecha, hora_inicio, hora_fin, sector):
        return None, f"Ya existe un turno programado en {sector} que se traslapa con ese horario."
    return datos.crear_turno(usuario_id, fecha, hora_inicio, hora_fin, sector), None


def editar_turno(turno_id, usuario_id, fecha, hora_inicio, hora_fin, sector, estado):
    if not (usuario_id and fecha and hora_inicio and hora_fin and sector and estado):
        return None, "Completa todos los campos del turno."
    if hora_fin <= hora_inicio:
        return None, "La hora de fin debe ser posterior a la hora de inicio."
    if datos.existe_turno_traslapado(fecha, hora_inicio, hora_fin, sector, excluir_turno_id=turno_id):
        return None, f"Ya existe otro turno programado en {sector} que se traslapa con ese horario."
    return datos.editar_turno(turno_id, usuario_id, fecha, hora_inicio, hora_fin, sector, estado), None


def registrar_actividad(usuario_id, tipo_accion, modulo, descripcion, entidad_id=None):
    from database import get_db
    db = get_db()
    db.execute(
        """INSERT INTO historial_actividades
           (usuario_id, tipo_accion, modulo, descripcion, entidad_id, fecha_hora)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (usuario_id, tipo_accion, modulo, descripcion, entidad_id, ahora_local().isoformat())
    )
    db.commit()


def alternar_turno_cancelado(turno_id):
    datos.alternar_turno_cancelado(turno_id)


# ------------------------------------------------------------------ avisos --

def listar_avisos(usuario_actual):
    """Comisariado ve todos (generales + personales de cualquiera); un usuario
    normal solo ve los avisos generales y los personales dirigidos a él."""
    if usuario_actual.rol == "comisariado":
        return datos.todos_los_avisos()
    return datos.avisos_visibles_para(usuario_actual.id)


def crear_aviso(titulo, contenido, tipo, alcance, autor, destinatario_ids=None):
    if not (titulo and contenido and tipo):
        return False, "Completa todos los campos del aviso."
    alcance = alcance if alcance in ("general", "personal") else "general"
    destinatario_ids = [int(i) for i in (destinatario_ids or []) if str(i).isdigit()]
    if alcance == "personal" and not destinatario_ids:
        return False, "Selecciona al menos un usuario destinatario para un aviso personal."
    datos.crear_aviso(titulo.strip(), contenido.strip(), tipo, alcance, autor,
                       hoy_local().isoformat(), ahora_local().strftime("%H:%M"), destinatario_ids)
    return True, None


def editar_aviso(aviso_id, titulo, contenido, tipo, alcance, destinatario_ids=None):
    if not (titulo and contenido and tipo):
        return False, "Completa todos los campos del aviso."
    alcance = alcance if alcance in ("general", "personal") else "general"
    destinatario_ids = [int(i) for i in (destinatario_ids or []) if str(i).isdigit()]
    if alcance == "personal" and not destinatario_ids:
        return False, "Selecciona al menos un usuario destinatario para un aviso personal."
    datos.editar_aviso(aviso_id, titulo.strip(), contenido.strip(), tipo, alcance, destinatario_ids)
    return True, None


def eliminar_aviso(aviso_id):
    datos.eliminar_aviso(aviso_id)


# -------------------------------------------------------------- actividades --

def listar_actividades():
    return datos.todas_las_actividades()


def crear_actividad(tipo, titulo, descripcion, fecha, hora, lugar, multa):
    if not (tipo and titulo and fecha and hora and lugar):
        return None, "Completa todos los campos obligatorios de la faena/reunión."
    error_fecha = _validar_fecha_no_pasada(fecha)
    if error_fecha:
        return None, error_fecha
    multa_val = None
    if multa not in (None, ""):
        try:
            multa_val = int(multa)
        except ValueError:
            return None, "La multa debe ser un número."
    actividad_id = datos.crear_actividad(tipo, titulo.strip(), (descripcion or "").strip(), fecha, hora, lugar.strip(), multa_val)
    return datos.actividad_por_id(actividad_id), None


def editar_actividad(actividad_id, tipo, titulo, descripcion, fecha, hora, lugar, multa):
    if not (tipo and titulo and fecha and hora and lugar):
        return None, "Completa todos los campos obligatorios de la faena/reunión."
    error_fecha = _validar_fecha_no_pasada(fecha)
    if error_fecha:
        return None, error_fecha
    multa_val = None
    if multa not in (None, ""):
        try:
            multa_val = int(multa)
        except ValueError:
            return None, "La multa debe ser un número."
    datos.editar_actividad(actividad_id, tipo, titulo.strip(), (descripcion or "").strip(), fecha, hora, lugar.strip(), multa_val)
    return datos.actividad_por_id(actividad_id), None


def alternar_asistencia(actividad_id, usuario_id):
    datos.alternar_asistencia(actividad_id, usuario_id)


# ------------------------------------------------------------------ multas --

def listar_multas(usuario_actual):
    """El comisariado ve todas las multas; un usuario normal únicamente las suyas."""
    if usuario_actual.rol == "comisariado":
        return datos.todas_las_multas()
    return datos.multas_de_usuario(usuario_actual.id)


def obtener_multa_visible(multa_id, usuario_actual):
    """Devuelve la multa solo si el usuario_actual tiene permiso para verla
    (comisariado, o el usuario específico al que pertenece la multa)."""
    multa = datos.multa_por_id(multa_id)
    if multa is None:
        return None
    if usuario_actual.rol != "comisariado" and multa.usuario_id != usuario_actual.id:
        return None
    return multa


def crear_multa(usuario_id, concepto, descripcion, monto_total, fecha, actividad_id, creado_por):
    if not (usuario_id and concepto and monto_total not in (None, "")):
        return None, "Completa el usuario, el concepto y el monto de la multa."
    # Las multas son solo para usuarios de la comunidad (rol 'usuario'),
    # nunca para la cuenta del comisariado.
    destinatario = datos.usuario_por_id(usuario_id)
    if destinatario is None or destinatario.rol != "usuario":
        return None, "Solo se pueden registrar multas a usuarios de la comunidad."
    try:
        monto_val = round(float(monto_total), 2)
    except ValueError:
        return None, "El monto debe ser un número."
    if monto_val <= 0:
        return None, "El monto debe ser mayor a cero."
    if not fecha:
        fecha = hoy_local().isoformat()
    else:
        error_fecha = _validar_fecha_no_pasada(fecha)
        if error_fecha:
            return None, error_fecha
    actividad_id_val = int(actividad_id) if actividad_id else None
    return datos.crear_multa(int(usuario_id), concepto.strip(), (descripcion or "").strip(),
                              monto_val, fecha, actividad_id_val, creado_por), None


def editar_multa(multa_id, concepto, descripcion, monto_total, fecha):
    if not (concepto and monto_total not in (None, "")):
        return None, "Completa el concepto y el monto de la multa."
    try:
        monto_val = round(float(monto_total), 2)
    except ValueError:
        return None, "El monto debe ser un número."
    multa_actual = datos.multa_por_id(multa_id)
    if multa_actual and monto_val < multa_actual.monto_pagado:
        return None, "El nuevo monto no puede ser menor a lo ya abonado."
    return datos.editar_multa(multa_id, concepto.strip(), (descripcion or "").strip(), monto_val, fecha), None


def eliminar_multa(multa_id):
    datos.eliminar_multa(multa_id)


def registrar_abono(multa_id, monto, registrado_por):
    multa = datos.multa_por_id(multa_id)
    if multa is None:
        return None, "La multa no existe."
    try:
        monto_val = round(float(monto), 2)
    except (ValueError, TypeError):
        return None, "El monto abonado debe ser un número."
    if monto_val <= 0:
        return None, "El monto abonado debe ser mayor a cero."
    if monto_val > multa.saldo:
        return None, f"El abono no puede exceder el saldo pendiente (${multa.saldo:.2f})."
    return datos.registrar_pago_multa(multa_id, monto_val, hoy_local().isoformat(), registrado_por), None


def historial_pagos_multa(multa_id):
    return datos.pagos_de_multa(multa_id)


# ----------------------------------------------------------------- cultivos --

def listar_cultivos():
    return datos.todos_los_cultivos()


def crear_cultivo(nombre, temporada, frecuencia_riego, consumo_agua, descripcion, accent):
    if not (nombre and temporada):
        return False, "Completa al menos el nombre y la temporada del cultivo."
    datos.crear_cultivo(nombre.strip(), temporada.strip(), (frecuencia_riego or "").strip(),
                         (consumo_agua or "").strip(), (descripcion or "").strip(), accent)
    return True, None


def eliminar_cultivo(cultivo_id):
    datos.eliminar_cultivo(cultivo_id)


# ----------------------------------------------------------------- usuarios --

def listar_usuarios():
    return datos.todos_los_usuarios()


def alternar_usuario_activo(usuario_id):
    datos.alternar_usuario_activo(usuario_id)
