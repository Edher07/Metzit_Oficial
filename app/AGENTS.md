# AGENTS.md — guía rápida para agentes de IA / nuevos colaboradores

## Qué es esto
Metzit — Agua y Pueblo es una aplicación web de gestión comunitaria del agua
de riego: turnos de riego, avisos comunitarios (generales y personales),
faenas y reuniones, multas por usuario, un catálogo de información agrícola
(cultivos) y un panel de administración de usuarios para el comisariado.

## Arquitectura
Flask (Python), pero a diferencia de otros proyectos hermanos **todo el
backend Python vive en una sola carpeta `backend/`** (sin subcarpetas por
capa):

- `backend/config.py` — configuración de la app (rutas, secretos, ruta de la base de datos).
- `backend/constantes.py` — paleta de colores, navegación (`NAV_ITEMS`), catálogos (sectores, estados de turno, tipos de aviso, alcances de aviso, estados de multa, colores de cultivo).
- `backend/modelos.py` — dataclasses que representan cada tabla (`Usuario`, `Turno`, `Aviso`, `Actividad`, `Multa`, `PagoMulta`, `Cultivo`).
- `backend/datos.py` — acceso a datos crudo sobre SQLite, agrupado por entidad, sin lógica de negocio.
- `backend/servicios.py` — lógica de negocio (autenticación, validaciones, resumen del dashboard, control de visibilidad de multas y avisos personales) que usa `datos.py`.
- `backend/sesion.py` — manejo de sesión de usuario (`login_required`, `admin_required`, `usuario_actual()`).
- `backend/rutas_*.py` — Blueprints de Flask (uno por sección: auth, dashboard, turnos, avisos, actividades, agricola, usuarios, multas); reciben la petición HTTP, llaman a `servicios.py` y renderizan una vista.
- `views/` — plantillas Jinja2, **una página HTML por pantalla visible** (login, inicio, turnos, avisos, actividades, agricola, usuarios, multas).
- `static/css/` — **una hoja de estilos por página**, más `utility.css` (clases de utilidad tipo Tailwind), `base.css` (reset + estilos de formularios) y `base_app.css` (layout de sidebar compartido).
- `static/js/` — JavaScript de cliente (toggles de formularios, interacciones de UI).

`database.py` (raíz de `app/`) crea el esquema SQLite y siembra los datos
iniciales la primera vez que se levanta el servidor. `app.py` arma la
aplicación Flask (fábrica `create_app()`) y registra los Blueprints. `run.py`
es el punto de entrada (`python run.py`).

## Convenciones
- Cada ruta de `backend/rutas_*.py` corresponde a una única plantilla en `views/`.
- Todas las plantillas de la app (excepto `login.html`) extienden `base_app.html`.
- No hay ORM: las consultas SQL viven exclusivamente en `backend/datos.py`.
- Las contraseñas se guardan con hash (`werkzeug.security`), nunca en texto plano.
- Solo el rol `comisariado` puede crear/editar turnos, avisos, faenas/reuniones,
  multas, cultivos y administrar usuarios (`admin_required`); el rol `usuario`
  tiene acceso de lectura y puede confirmar su propia asistencia a faenas/reuniones.
- **Registro de usuarios**: no existe autorregistro público. Únicamente el
  comisariado da de alta cuentas nuevas, desde "Usuarios → + Nuevo usuario"
  (`rutas_usuarios.crear`). La ruta `/registro` ya no existe.
- **Usuarios sin borrado físico**: un usuario nunca se elimina de la base de
  datos, solo se activa/desactiva (`usuarios.alternar_activo`). Esto evita que
  turnos, multas o avisos personales queden huérfanos o muestren
  "(usuario eliminado)".
- **Editar en vez de eliminar**: turnos (`turnos.editar`), faenas/reuniones
  (`actividades.editar`) y multas (`multas.editar`) se editan en lugar de
  eliminarse, para conservar el historial comunitario.
- **Multas privadas**: una multa solo la puede ver el comisariado o el usuario
  al que pertenece (`servicios.obtener_multa_visible` / `listar_multas`). Los
  abonos se registran en `multa_pagos` y el saldo pendiente
  (`monto_total - monto_pagado`) se recalcula automáticamente junto con el
  estado (`pendiente` / `parcial` / `pagada`).
- **Avisos generales y personales**: un aviso tiene `alcance` = `general`
  (visible para todos) o `personal` (visible solo para el comisariado y los
  usuarios listados en `aviso_destinatarios`).
- `turnos.usuario_id` y `multas.usuario_id` son claves foráneas reales a
  `usuarios` (`NOT NULL`), y la asistencia a `actividades` se guarda en la
  tabla de unión `actividad_participantes`.

## Cómo correrlo localmente
```
pip install -r requirements.txt
python run.py
```
El servidor crea `metzit.sqlite3` automáticamente en el primer arranque.
