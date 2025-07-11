# app/models/pedido_model.py
from app import db
from datetime import datetime

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    pedido_id = db.Column(db.Integer, primary_key=True)
    perfil_cliente_id = db.Column(db.Integer, db.ForeignKey('perfiles_cliente.perfil_cliente_id'), nullable=False)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    estado = db.Column(db.String(50), nullable=False, default='pendiente', index=True)
    monto_total = db.Column(db.Numeric(10, 2), nullable=True)
    path_comprobante = db.Column(db.String(255), nullable=True)

    # --- NUEVO CAMPO ---
    fecha_espera_maxima = db.Column(db.DateTime, nullable=True)

    perfil_cliente = db.relationship('PerfilCliente', back_populates='pedidos')
    detalles = db.relationship('DetallePedido', back_populates='pedido', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido {self.pedido_id} - Estado: {self.estado}>"