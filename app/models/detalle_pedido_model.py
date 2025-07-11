# app/models/detalle_pedido_model.py
from app import db
from sqlalchemy.dialects.postgresql import JSONB
import decimal

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    
    detalle_pedido_id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.pedido_id', ondelete='CASCADE'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.producto_id', ondelete='SET NULL'), nullable=True)
    
    respuestas_requisitos = db.Column(JSONB)
    completo = db.Column(db.Boolean, default=False, nullable=False)
    
    nombre_producto_historico = db.Column(db.String(200), nullable=False)
    sku_historico = db.Column(db.String(50))
    
    # --- CAMPOS DE PRECIO ACTUALIZADOS SEGÚN EL PLAN APROBADO ---
    
    # Guarda el precio de referencia al momento de añadir al carrito.
    precio_unitario_historico = db.Column(db.Numeric(10, 2), nullable=False)
    
    # NUEVO CAMPO: Guarda el precio final pagado (puede ser menor por compra en grupo).
    precio_pagado = db.Column(db.Numeric(10, 2), nullable=True)


    # --- RELACIONES ---
    pedido = db.relationship('Pedido', back_populates='detalles')
    producto = db.relationship('Producto', back_populates='detalles_pedido')

    def __repr__(self):
        return f"<DetallePedido {self.detalle_pedido_id} para Pedido {self.pedido_id}>"