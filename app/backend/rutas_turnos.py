from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
import datos
from sesion import login_required, admin_required, usuario_actual
from constantes import SECTORES, ESTADOS_TURNO, hoy as hoy_local, ahora as ahora_local

bp = Blueprint("turnos", __name__)


@bp.route("/turnos")
@login_required
def listar():
    filtro = request.args.get("estado", "todos")
    turnos = servicios.listar_turnos(filtro)
    return render_template(
        "turnos.html", turnos=turnos, filtro=filtro,
        sectores=SECTORES, estados=ESTADOS_TURNO,
        usuarios=datos.todos_los_usuarios(),
        hoy=hoy_local().isoformat(),
        ahora=ahora_local().strftime("%H:%M"),
    )


@bp.route("/turnos/nuevo", methods=["POST"])
@admin_required
def crear():
    usuario_id = request.form.get("usuario_id", type=int)
    _, error = servicios.crear_turno(
        usuario_id=usuario_id,
        fecha=request.form.get("fecha", ""),
        hora_inicio=request.form.get("hora_inicio", ""),
        hora_fin=request.form.get("hora_fin", ""),
        sector=request.form.get("sector", ""),
    )
    if error:
        flash(error, "error")
    else:
        flash("Turno creado correctamente.", "success")
    return redirect(url_for("turnos.listar"))


@bp.route("/turnos/<int:turno_id>/cancelar", methods=["POST"])
@admin_required
def alternar_cancelado(turno_id):
    turno = datos.turno_por_id(turno_id)
    servicios.alternar_turno_cancelado(turno_id)
    servicios.registrar_actividad(
        usuario_id=usuario_actual().id,
        tipo_accion='cancelar_turno',
        modulo='turnos',
        descripcion=f'Canceló turno de {turno.sector} el {turno.fecha}',
        entidad_id=turno_id
    )
    return redirect(url_for("turnos.listar", estado=request.args.get("estado", "todos")))


@bp.route("/turnos/<int:turno_id>/editar", methods=["POST"])
@admin_required
def editar(turno_id):
    # El comisariado edita el turno en vez de eliminarlo, así se conserva el
    # historial y nunca aparece un turno huérfano o "(usuario eliminado)".
    _, error = servicios.editar_turno(
        turno_id,
        usuario_id=request.form.get("usuario_id", type=int),
        fecha=request.form.get("fecha", ""),
        hora_inicio=request.form.get("hora_inicio", ""),
        hora_fin=request.form.get("hora_fin", ""),
        sector=request.form.get("sector", ""),
        estado=request.form.get("estado", ""),
    )
    flash("Turno actualizado correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("turnos.listar", estado=request.args.get("estado", "todos")))
