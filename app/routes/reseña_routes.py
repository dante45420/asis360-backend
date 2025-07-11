# app/routes/reseña_routes.py
from app import db
from app.models import Reseña, Pedido, DetallePedido, Producto
from typing import List, Optional
from sqlalchemy.orm import aliased
from sqlalchemy import and_, distinct

class ReseñaRoute:
    @staticmethod
    def create(perfil_cliente_id: int, producto_id: int, calificacion: int, comentario: str) -> Reseña:
        nueva_reseña = Reseña(
            perfil_cliente_id=perfil_cliente_id,
            producto_id=producto_id,
            calificacion=calificacion,
            comentario=comentario
        )
        db.session.add(nueva_reseña)
        db.session.commit()
        return nueva_reseña

    @staticmethod
    def update(reseña_id: int, data: dict) -> Optional[Reseña]:
        reseña = Reseña.query.get(reseña_id)
        if reseña:
            reseña.calificacion = data.get('calificacion', reseña.calificacion)
            reseña.comentario = data.get('comentario', reseña.comentario)
            db.session.commit()
        return reseña

    @staticmethod
    def get_by_perfil_and_producto(perfil_cliente_id: int, producto_id: int) -> Optional[Reseña]:
        return Reseña.query.filter_by(perfil_cliente_id=perfil_cliente_id, producto_id=producto_id).first()

    @staticmethod
    def get_productos_para_reseña(perfil_cliente_id: int) -> List[Producto]:
        """
        --- LÓGICA COMPLETAMENTE REFACTORIZADA Y CORREGIDA ---
        Obtiene una lista de productos de pedidos 'completos' que aún no han sido reseñados por el cliente.
        """
        # 1. Subconsulta: Obtiene los IDs de todos los productos únicos que el cliente
        #    ha comprado en pedidos con estado 'completo'.
        productos_comprados_ids = db.session.query(distinct(DetallePedido.producto_id))\
            .join(Pedido)\
            .filter(
                Pedido.perfil_cliente_id == perfil_cliente_id,
                Pedido.estado == 'completo',
                DetallePedido.producto_id.isnot(None) # Ignoramos detalles si el producto fue borrado
            ).subquery()

        # 2. Subconsulta: Obtiene los IDs de los productos que este cliente YA ha reseñado.
        productos_reseñados_ids = db.session.query(Reseña.producto_id)\
            .filter(Reseña.perfil_cliente_id == perfil_cliente_id)\
            .subquery()

        # 3. Query Final: Busca los productos cuyo ID está en la lista de comprados
        #    pero NO está en la lista de reseñados.
        productos_pendientes = db.session.query(Producto)\
            .filter(
                Producto.producto_id.in_(productos_comprados_ids),
                Producto.producto_id.notin_(productos_reseñados_ids)
            ).order_by(Producto.nombre_producto).all()
        
        return productos_pendientes
    
    @staticmethod
    def get_all_for_profile(perfil_cliente_id: int) -> List[Reseña]:
        """NUEVO: Obtiene todas las reseñas de un perfil de cliente."""
        return Reseña.query.filter_by(perfil_cliente_id=perfil_cliente_id)\
            .order_by(Reseña.fecha_creacion.desc()).all()