# app/models/perfil_proveedor_model.py
from app import db

class PerfilProveedor(db.Model):
    __tablename__ = 'perfiles_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False, unique=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.proveedor_id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='perfil_proveedor')
    proveedor = db.relationship('Proveedor', back_populates='miembros')

    def __repr__(self):
        return f"<PerfilProveedor: Usuario {self.usuario_id} en Proveedor {self.proveedor_id}>"