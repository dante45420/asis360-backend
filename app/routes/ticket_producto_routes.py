# app/routes/ticket_producto_routes.py
from app import db
from app.models import TicketProducto
from typing import List, Optional

class TicketProductoRoute:
    @staticmethod
    def get_all() -> List[TicketProducto]:
        return TicketProducto.query.order_by(TicketProducto.ticket_id.desc()).all()

    @staticmethod
    def find_incomplete_by_client(perfil_cliente_id: int) -> Optional[TicketProducto]:
        """Busca por perfil_cliente_id."""
        return TicketProducto.query.filter_by(perfil_cliente_id=perfil_cliente_id, estado='incompleto').first()

    @staticmethod
    def create_incomplete(perfil_cliente_id: int) -> TicketProducto:
        """Crea un ticket para un perfil_cliente_id."""
        ticket = TicketProducto(
            perfil_cliente_id=perfil_cliente_id,
            estado='incompleto'
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket

    @staticmethod
    def update(ticket_id: int, data: dict):
        ticket = TicketProducto.query.get(ticket_id)
        if ticket:
            for key, value in data.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)
            db.session.commit()
        return ticket
    
    @staticmethod
    def get_by_status(statuses: List[str]) -> List[TicketProducto]:
        return TicketProducto.query.filter(TicketProducto.estado.in_(statuses)).order_by(TicketProducto.fecha_creacion.desc()).all()
    
    @staticmethod
    def create_ticket_completo(perfil_cliente_id: int, nombre_producto: str, descripcion: str) -> TicketProducto:
        """NUEVO: Crea un ticket directamente con todos los datos desde la web."""
        ticket = TicketProducto(
            perfil_cliente_id=perfil_cliente_id,
            nombre_producto_deseado=nombre_producto,
            descripcion=descripcion,
            estado='nuevo' # Los tickets de la web entran como nuevos directamente
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket
    
    @staticmethod
    def get_by_profile_id(perfil_cliente_id: int) -> List[TicketProducto]:
        """Obtiene todos los tickets de un perfil de cliente específico."""
        return TicketProducto.query.filter_by(perfil_cliente_id=perfil_cliente_id)\
            .order_by(TicketProducto.fecha_creacion.desc()).all()
    
    @staticmethod
    def crear_ticket_de_pedido_bot(perfil_cliente_id: int, descripcion_pedido: str) -> TicketProducto:
        """
        Crea un nuevo ticket de producto a partir de una solicitud del chatbot.
        """
        nuevo_ticket = TicketProducto(
            perfil_cliente_id=perfil_cliente_id,
            nombre_producto_deseado="Pedido realizado con el Bot", # Título solicitado
            descripcion=descripcion_pedido, # El pedido detallado por el usuario
            estado='nuevo'  # Un estado inicial claro
        )
        db.session.add(nuevo_ticket)
        db.session.commit()
        return nuevo_ticket