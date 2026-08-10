from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
import datos
from sesion import login_required, admin_required, usuario_actual
from constantes import ESTADOS_MULTA, hoy as hoy_local

bp = Blueprint("multas", __name__)


@bp.route("/multas")
@login_required
def listar():
    u = usuario_actual()
    multas = servicios.listar_multas(u)
    usuarios = datos.usuarios_multables() if u.rol == "comisariado" else []
    pagos_por_multa = {m.id: servicios.historial_pagos_multa(m.id) for m in multas}
    return render_template(
        "multas.html", multas=multas, estados=ESTADOS_MULTA,
        usuarios=usuarios, hoy=hoy_local().isoformat(),
        pagos_por_multa=pagos_por_multa,
    )


@bp.route("/multas/nueva", methods=["POST"])
@admin_required
def crear():
    u = usuario_actual()
    _, error = servicios.crear_multa(
        usuario_id=request.form.get("usuario_id", type=int),
        concepto=request.form.get("concepto", ""),
        descripcion=request.form.get("descripcion", ""),
        monto_total=request.form.get("monto_total", ""),
        fecha=request.form.get("fecha", ""),
        actividad_id=request.form.get("actividad_id", ""),
        creado_por=u.nombre,
    )
    flash("Multa registrada correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("multas.listar"))


@bp.route("/multas/<int:multa_id>/editar", methods=["POST"])
@admin_required
def editar(multa_id):
    # El comisariado edita la multa en vez de eliminarla, así el usuario
    # afectado conserva el detalle e historial de sus abonos.
    _, error = servicios.editar_multa(
        multa_id,
        concepto=request.form.get("concepto", ""),
        descripcion=request.form.get("descripcion", ""),
        monto_total=request.form.get("monto_total", ""),
        fecha=request.form.get("fecha", ""),
    )
    flash("Multa actualizada correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("multas.listar"))


@bp.route("/multas/<int:multa_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(multa_id):
    servicios.eliminar_multa(multa_id)
    flash("Multa eliminada.", "success")
    return redirect(url_for("multas.listar"))


@bp.route("/multas/<int:multa_id>/abonar", methods=["POST"])
@admin_required
def abonar(multa_id):
    u = usuario_actual()
    _, error = servicios.registrar_abono(
        multa_id, request.form.get("monto", ""), u.nombre,
    )
    flash("Abono registrado correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("multas.listar"))
