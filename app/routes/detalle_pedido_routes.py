# app/routes/detalle_pedido_routes.py

from app import db
from app.models.detalle_pedido_model import DetallePedido
from app.models.producto_model import Producto
from typing import Optional, List
from sqlalchemy.orm.attributes import flag_modified
import decimal

class DetallePedidoRoute:
    """
    Gestiona las operaciones de la base de datos para la entidad DetallePedido.
    """

    @staticmethod
    def create_detalle(pedido_id: int, producto_id: int, nombre_historico: str, sku_historico: str, precio_historico: float):
        nuevo_detalle = DetallePedido(
            pedido_id=pedido_id, producto_id=producto_id, respuestas_requisitos={},
            nombre_producto_historico=nombre_historico, sku_historico=sku_historico,
            precio_unitario_historico=precio_historico
        )
        db.session.add(nuevo_detalle)
        db.session.commit()
        return nuevo_detalle

    @staticmethod
    def get_by_id(detalle_id: int) -> Optional[DetallePedido]:
        """Obtiene un detalle de pedido por su ID primario."""
        return DetallePedido.query.get(detalle_id)

    @staticmethod
    def update_respuestas(detalle_id: int, nuevas_respuestas: dict):
        """
        Añade o actualiza las respuestas en la columna JSONB RespuestasRequisitos.
        """
        detalle = DetallePedido.query.get(detalle_id)
        if detalle:
            if detalle.respuestas_requisitos is None:
                detalle.respuestas_requisitos = {}
            
            detalle.respuestas_requisitos.update(nuevas_respuestas)
            
            flag_modified(detalle, "respuestas_requisitos")
            
            db.session.commit()
            print(f"Respuestas actualizadas para detalle_pedido_id {detalle_id}.")

    @staticmethod
    def mark_as_complete(detalle_id: int):
        """
        Marca un DetallePedido como completo y, crucialmente, calcula y guarda su precio histórico.
        """
        detalle = DetallePedido.query.get(detalle_id)
        if detalle and not detalle.completo:
            producto = Producto.query.get(detalle.producto_id)
            if producto:
                # Lógica para determinar el precio basado en las respuestas (ej. formato)
                # Esto es un ejemplo, deberás adaptarlo a tu lógica de precios específica.
                precio_calculado = producto.precio_base
                formato_elegido = detalle.respuestas_requisitos.get('Formato')
                if formato_elegido:
                    # Asume que tienes una forma de obtener el precio por variación
                    precio_variacion = next((p.precio_unitario for p in producto.precios if p.variacion == formato_elegido), producto.precio_base)
                    precio_calculado = precio_variacion or producto.precio_base
                
                detalle.precio_unitario_historico = decimal.Decimal(precio_calculado)
            
            detalle.completo = True
            db.session.commit()
            print(f"Detalle_pedido_id {detalle_id} marcado como completo con precio {_format_price(detalle.precio_unitario_historico)}.")

    
    @staticmethod
    def add_item_to_order(pedido_id: int, producto_id: int, nombre_producto: str, precio_unitario: decimal, sku: str, respuestas: dict) -> DetallePedido:
        """Añade un nuevo ítem a un pedido (carrito), inicializando ambos campos de precio."""
        detalle = DetallePedido(
            pedido_id=pedido_id,
            producto_id=producto_id,
            nombre_producto_historico=nombre_producto,
            sku_historico=sku,
            respuestas_requisitos=respuestas,
            completo=True,
            # Se inicializan ambos campos con el precio individual del momento.
            precio_unitario_historico=precio_unitario,
            precio_pagado=precio_unitario
        )
        db.session.add(detalle)
        db.session.commit()
        return detalle

    @staticmethod
    def remove_item_from_order(detalle_id: int) -> bool:
        """Elimina un ítem de un pedido (carrito)."""
        detalle = DetallePedido.query.get(detalle_id)
        if detalle:
            db.session.delete(detalle)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_by_ids(detalle_ids: List[int]) -> List[DetallePedido]:
        """
        Obtiene una lista de objetos DetallePedido a partir de una lista de IDs.
        """
        if not detalle_ids:
            return []
        
        return db.session.query(DetallePedido).filter(
            DetallePedido.detalle_pedido_id.in_(detalle_ids)
        ).all()
    
    @staticmethod
    def update_precio_pagado(detalle_id: int, nuevo_precio: decimal.Decimal) -> Optional[DetallePedido]:
        """Actualiza el precio final pagado de un único detalle de pedido."""
        detalle = DetallePedido.query.get(detalle_id)
        if detalle:
            detalle.precio_pagado = nuevo_precio
            # El commit se hará en la capa de API para agrupar todas las actualizaciones.
        return detalle
    
    # --- FUNCIÓN NUEVA AÑADIDA ---
    @staticmethod
    def create_incomplete_detalle(pedido_id: int, producto_id: int, nombre_historico: str, sku_historico: Optional[str]) -> DetallePedido:
        """Crea un nuevo 'detalle de pedido' marcado como incompleto."""
        DetallePedido.query.filter_by(pedido_id=pedido_id, completo=False).delete()
        
        nuevo_detalle = DetallePedido(
            pedido_id=pedido_id,
            producto_id=producto_id,
            nombre_producto_historico=nombre_historico,
            sku_historico=sku_historico,
            completo=False,
            respuestas_requisitos={},
            precio_unitario_historico=0 
        )
        db.session.add(nuevo_detalle)
        db.session.commit()
        return nuevo_detalle

    @staticmethod
    def find_incomplete_by_order(pedido_id: int) -> Optional[DetallePedido]:
        """Encuentra el último detalle incompleto de un pedido."""
        return DetallePedido.query.filter_by(pedido_id=pedido_id, completo=False).order_by(DetallePedido.detalle_pedido_id.desc()).first()