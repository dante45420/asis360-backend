# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
from config import Config

db = SQLAlchemy()

def create_app():
    """
    Función factory para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Importar y registrar los Blueprints
    from .api import webhook_route, auth_routes, admin_api_routes, portal_api_routes
    app.register_blueprint(webhook_route.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_api_routes.bp)
    app.register_blueprint(portal_api_routes.bp)

    # Inicializar CORS
    frontend_url = app.config.get('FRONTEND_URL')
    if frontend_url:
        CORS(
            app, 
            resources={r"/api/.*": {"origins": frontend_url}}, 
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            supports_credentials=True
        )
    else:
        print("ADVERTENCIA: FRONTEND_URL no está definida. CORS no estará activo.")

    return app

def create_db_tables(app):
    """Función de ayuda para crear tablas (actualizada)."""
    with app.app_context():
        # Importar todos los nuevos modelos para asegurar que db.create_all() los vea.
        from app.models import (
            Usuario, Organizacion, PerfilCliente, Proveedor, PerfilProveedor,
            Producto, RequisitoProducto, PreciosProducto, Pedido, DetallePedido,
            Conversacion, Mensaje, SoporteResolucion, TicketProducto
        )
        db.create_all()
        print("Tablas de la base de datos creadas exitosamente.")

def drop_db_tables(app):
    """Función de ayuda para eliminar tablas (actualizada)."""
    with app.app_context():
        # ... (La lógica de drop_db_tables puede permanecer igual ya que elimina todas las tablas sin necesidad de importarlas explícitamente)
        try:
            print("Eliminando todas las tablas con CASCADE...")
            db.session.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
            db.session.commit()
            print("Tablas de la base de datos eliminadas exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"Ocurrió un error al eliminar las tablas: {e}")