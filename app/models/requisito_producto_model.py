# app/models/requisito_producto_model.py
from app import db
from sqlalchemy.dialects.postgresql import JSONB

class RequisitoProducto(db.Model):
    __tablename__ = 'requisitos_producto'

    requisito_id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.producto_id'), nullable=False)
    nombre_requisito = db.Column(db.String(100), nullable=False)
    tipo_dato = db.Column(db.String(50), default='Texto')
    tipo_validacion = db.Column(db.String(50), default='texto_simple', nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)
    
    # --- NUEVA COLUMNA AÑADIDA ---
    # Almacenará una lista de opciones predefinidas, ej: ['Rojo', 'Azul', 'Verde']
    opciones = db.Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<RequisitoProducto {self.requisito_id}: {self.nombre_requisito}>"