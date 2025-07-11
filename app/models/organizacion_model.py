# app/models/organizacion_model.py
from app import db

class Organizacion(db.Model):
    __tablename__ = 'organizaciones'

    organizacion_id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(150), nullable=False)
    rut_empresa = db.Column(db.String(12), unique=True, nullable=True)
    direccion = db.Column(db.Text, nullable=True)

    # Relación uno-a-muchos con PerfilCliente
    perfiles_cliente = db.relationship('PerfilCliente', backref='organizacion', lazy='dynamic')

    def __repr__(self):
        return f"<Organizacion {self.organizacion_id}: {self.nombre_empresa}>"