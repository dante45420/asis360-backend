from app import db
from sqlalchemy.dialects.postgresql import JSONB

class PreciosProducto(db.Model):
    """
    Modelo para almacenar los precios de un producto.
    Ahora incluye la capacidad de definir precios por variante (basado en
    requisitos) y por volumen (basado en cantidad).
    """
    __tablename__ = 'precios_producto'

    precio_id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.producto_id', ondelete='CASCADE'), nullable=False)
    
    # Almacenará la combinación de requisitos que definen esta variante.
    # Ej: {'Formato': '1 Litro', 'Envase': 'Vidrio'}
    # Si es NULL, representa un precio base o por defecto.
    variante_requisitos = db.Column(JSONB, nullable=True, index=True) 
    
    # SKU específico para esta variante, útil para la gestión de inventario.
    sku_variante = db.Column(db.String(100), nullable=True, unique=True)
    
    # La cantidad mínima sigue siendo importante para precios por volumen en CADA variante.
    cantidad_minima = db.Column(db.Integer, default=1, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<Precio para Producto {self.producto_id} - Variante: {self.variante_requisitos}>"