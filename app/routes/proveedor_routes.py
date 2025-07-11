# app/routes/proveedor_routes.py

from app import db
from app.models.proveedor_model import Proveedor
from app.models.producto_model import Producto
from typing import List, Optional

class ProveedorRoute:
    """
    Gestiona las operaciones de la base de datos para la entidad Proveedor.
    """

    @staticmethod
    def get_all() -> list:
        return Proveedor.query.all()

    @staticmethod
    def get_by_id(proveedor_id: int) -> Optional[Proveedor]:
        """Obtiene un proveedor por su ID."""
        return Proveedor.query.get(proveedor_id)

    @staticmethod
    def create(data: dict) -> Proveedor:
        nuevo_proveedor = Proveedor(
            nombre=data['nombre'],
            info_contacto=data.get('info_contacto'),
            calidad_servicio=data.get('calidad_servicio', 10)
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        return nuevo_proveedor

    @staticmethod
    def update(proveedor_id: int, data: dict) -> Optional[Proveedor]:
        proveedor = Proveedor.query.get(proveedor_id)
        if not proveedor:
            return None
        for key, value in data.items():
            if hasattr(proveedor, key):
                setattr(proveedor, key, value)
        db.session.commit()
        return proveedor

    @staticmethod
    def delete(proveedor_id: int) -> bool:
        proveedor = Proveedor.query.get(proveedor_id)
        if proveedor:
            # Marcar productos como inactivos
            productos = Producto.query.filter_by(proveedor_id=proveedor_id).all()
            for producto in productos:
                producto.activo = False
            db.session.commit()
            db.session.delete(proveedor)
            db.session.commit()
            return True
        return False