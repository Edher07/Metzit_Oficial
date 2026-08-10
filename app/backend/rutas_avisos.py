from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
import datos
from sesion import login_required, admin_required, usuario_actual
from constantes import TIPOS_AVISO, ALCANCES_AVISO

bp = Blueprint("avisos", __name__)


@bp.route("/avisos")
@login_required
def listar():
    u = usuario_actual()
    avisos = servicios.listar_avisos(u)
    usuarios = datos.todos_los_usuarios() if u.rol == "comisariado" else []
    return render_template("avisos.html", avisos=avisos, tipos=TIPOS_AVISO,
                            alcances=ALCANCES_AVISO, usuarios=usuarios)


@bp.route("/avisos/nuevo", methods=["POST"])
@admin_required
def crear():
    u = usuario_actual()
    ok, error = servicios.crear_aviso(
        titulo=request.form.get("titulo", ""),
        contenido=request.form.get("contenido", ""),
        tipo=request.form.get("tipo", ""),
        alcance=request.form.get("alcance", "general"),
        autor=u.nombre,
        destinatario_ids=request.form.getlist("destinatarios"),
    )
    flash("Aviso publicado correctamente." if ok else error, "success" if ok else "error")
    return redirect(url_for("avisos.listar"))


@bp.route("/avisos/<int:aviso_id>/editar", methods=["POST"])
@admin_required
def editar(aviso_id):
    ok, error = servicios.editar_aviso(
        aviso_id,
        titulo=request.form.get("titulo", ""),
        contenido=request.form.get("contenido", ""),
        tipo=request.form.get("tipo", ""),
        alcance=request.form.get("alcance", "general"),
        destinatario_ids=request.form.getlist("destinatarios"),
    )
    flash("Aviso actualizado correctamente." if ok else error, "success" if ok else "error")
    return redirect(url_for("avisos.listar"))


@bp.route("/avisos/<int:aviso_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(aviso_id):
    servicios.eliminar_aviso(aviso_id)
    flash("Aviso eliminado.", "success")
    return redirect(url_for("avisos.listar"))
