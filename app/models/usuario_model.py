# app/models/usuario_model.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    usuario_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default='cliente', index=True)
    fecha_registro = db.Column(db.TIMESTAMP, server_default=db.func.now())

    # --- CAMPOS NUEVOS PARA VERIFICACIÓN ---
    codigo_verificacion = db.Column(db.String(6), nullable=True)
    codigo_expiracion = db.Column(db.TIMESTAMP, nullable=True)

    # Relaciones
    perfil_cliente = db.relationship('PerfilCliente', back_populates='usuario', uselist=False, cascade="all, delete-orphan")
    perfil_proveedor = db.relationship('PerfilProveedor', back_populates='usuario', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None: return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.usuario_id}: {self.nombre}>"