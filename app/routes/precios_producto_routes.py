from app import db
from app.models.precios_producto_model import PreciosProducto
from typing import Optional, List

class PreciosProductoRoute:
    """
    Gestiona las operaciones de la base de datos para la entidad PreciosProducto.
    """

    @staticmethod
    def create(data: dict) -> PreciosProducto:
        nuevo_precio = PreciosProducto(
            producto_id=data['producto_id'],
            variante_requisitos=data.get('variante_requisitos'),
            cantidad_minima=data['cantidad_minima'],
            precio_unitario=data['precio_unitario']
        )
        db.session.add(nuevo_precio)
        db.session.commit()
        return nuevo_precio

    @staticmethod
    def update(precio_id: int, data: dict) -> Optional[PreciosProducto]:
        precio = PreciosProducto.query.get(precio_id)
        if not precio:
            return None
        for key, value in data.items():
            if hasattr(precio, key):
                setattr(precio, key, value)
        db.session.commit()
        return precio

    @staticmethod
    def delete(precio_id: int) -> bool:
        precio = PreciosProducto.query.get(precio_id)
        if precio:
            db.session.delete(precio)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_price_for_quantity(producto_id: int, variante: dict, cantidad: int) -> Optional[PreciosProducto]:
        """
        Encuentra el mejor precio unitario para un producto, variante y cantidad específicos.
        """
        # (Esta lógica puede ser más compleja, pero una versión simple es buscar el tramo más alto que se cumpla)
        precios_aplicables = PreciosProducto.query.filter(
            PreciosProducto.producto_id == producto_id,
            PreciosProducto.variante_requisitos == (variante if PreciosProducto.variante_requisitos is not None else None),
            PreciosProducto.cantidad_minima <= cantidad
        ).order_by(PreciosProducto.cantidad_minima.desc()).first()
        
        return precios_aplicables