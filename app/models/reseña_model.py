# app/models/reseña_model.py
from app import db
from datetime import datetime

class Reseña(db.Model):
    __tablename__ = 'reseñas'

    reseña_id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.producto_id'), nullable=False)
    perfil_cliente_id = db.Column(db.Integer, db.ForeignKey('perfiles_cliente.perfil_cliente_id'), nullable=False)
    
    calificacion = db.Column(db.Integer, nullable=False) # Calificación de 1 a 5
    comentario = db.Column(db.Text, nullable=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship('Producto', backref='reseñas')
    perfil_cliente = db.relationship('PerfilCliente', backref='reseñas')

    def __repr__(self):
        return f"<Reseña {self.reseña_id} para Producto {self.producto_id}>"