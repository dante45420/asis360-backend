# app/models/proveedor_model.py
from app import db

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    proveedor_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    info_contacto = db.Column(db.Text)
    calidad_servicio = db.Column(db.Integer)
    esta_activo = db.Column(db.Boolean, default=True, nullable=False)

    productos = db.relationship('Producto', backref='proveedor', lazy=True)
    miembros = db.relationship('PerfilProveedor', back_populates='proveedor')

    def __repr__(self):
        return f"<Proveedor {self.proveedor_id}: {self.nombre}>"