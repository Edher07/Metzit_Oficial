"""Fábrica de la aplicación Flask — Metzit — Agua y Pueblo."""
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(APP_DIR, "backend")


for _path in (APP_DIR, BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from flask import Flask, render_template

import database
from config import Config, STATIC_DIR, VIEWS_DIR
from constantes import COLORES, FONT_BODY, FONT_HEADING, NAV_ITEMS
from sesion import usuario_actual


def create_app():
    app = Flask(
        __name__,
        static_folder=STATIC_DIR,
        static_url_path="/static",
        template_folder=VIEWS_DIR,
    )
    app.config.from_object(Config)

    database.init_app(app)
    with app.app_context():
        database.init_db(app)

    from rutas_auth import bp as auth_bp
    from rutas_dashboard import bp as dashboard_bp
    from rutas_turnos import bp as turnos_bp
    from rutas_avisos import bp as avisos_bp
    from rutas_actividades import bp as actividades_bp
    from rutas_agricola import bp as agricola_bp
    from rutas_usuarios import bp as usuarios_bp
    from rutas_multas import bp as multas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(turnos_bp)
    app.register_blueprint(avisos_bp)
    app.register_blueprint(actividades_bp)
    app.register_blueprint(agricola_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(multas_bp)

    @app.context_processor
    def inyectar_globales():
        return dict(
            colores=COLORES,
            font_body=FONT_BODY,
            font_heading=FONT_HEADING,
            nav_items=NAV_ITEMS,
            usuario_actual=usuario_actual(),
        )

    @app.errorhandler(404)
    def no_encontrado(_e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
