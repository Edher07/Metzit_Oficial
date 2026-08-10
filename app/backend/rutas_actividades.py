from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

import servicios
from database import get_db
from sesion import login_required, admin_required, usuario_actual
from constantes import hoy as hoy_local

bp = Blueprint("actividades", __name__)


@bp.route("/actividades")
@login_required
def listar():
    actividades = servicios.listar_actividades()
    return render_template(
        "actividades.html", actividades=actividades, usuario=usuario_actual(),
        hoy=hoy_local().isoformat(),
    )


@bp.route("/actividades/nueva", methods=["POST"])
@admin_required
def crear():
    _, error = servicios.crear_actividad(
        tipo=request.form.get("tipo", ""),
        titulo=request.form.get("titulo", ""),
        descripcion=request.form.get("descripcion", ""),
        fecha=request.form.get("fecha", ""),
        hora=request.form.get("hora", ""),
        lugar=request.form.get("lugar", ""),
        multa=request.form.get("multa", ""),
    )
    flash("Faena/reunión creada correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("actividades.listar"))


@bp.route("/actividades/<int:actividad_id>/editar", methods=["POST"])
@admin_required
def editar(actividad_id):
    # El comisariado edita la faena/reunión en vez de eliminarla, para
    # conservar el historial de asistencia y las multas asociadas.
    _, error = servicios.editar_actividad(
        actividad_id,
        tipo=request.form.get("tipo", ""),
        titulo=request.form.get("titulo", ""),
        descripcion=request.form.get("descripcion", ""),
        fecha=request.form.get("fecha", ""),
        hora=request.form.get("hora", ""),
        lugar=request.form.get("lugar", ""),
        multa=request.form.get("multa", ""),
    )
    flash("Faena/reunión actualizada correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("actividades.listar"))


@bp.route("/actividades/<int:actividad_id>/asistencia", methods=["POST"])
@login_required
def alternar_asistencia(actividad_id):
    u = usuario_actual()
    servicios.alternar_asistencia(actividad_id, u.id)
    return redirect(url_for("actividades.listar"))


@bp.route('/api/actividades', methods=['GET'])
@login_required
def obtener_historial():
    usuario_id = request.args.get('usuario_id')
    fecha_inicio = request.args.get('fecha_inicio')  # '2026-08-01'
    fecha_fin = request.args.get('fecha_fin')          # '2026-08-06'
    hora_inicio = request.args.get('hora_inicio')       # '08:00'
    hora_fin = request.args.get('hora_fin')             # '18:00'

    query = "SELECT * FROM historial_actividades WHERE 1=1"
    params = []

    if usuario_id:
        query += " AND usuario_id = ?"
        params.append(usuario_id)
    if fecha_inicio and fecha_fin:
        query += " AND date(fecha_hora) BETWEEN ? AND ?"
        params.extend([fecha_inicio, fecha_fin])
    if hora_inicio and hora_fin:
        query += " AND time(fecha_hora) BETWEEN ? AND ?"
        params.extend([hora_inicio, hora_fin])

    query += " ORDER BY fecha_hora DESC"
    resultados = get_db().execute(query, params).fetchall()
    return jsonify([dict(r) for r in resultados])
