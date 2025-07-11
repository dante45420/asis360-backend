# app/routes/soporte_resolucion_routes.py
from app import db
from app.models import SoporteResolucion, Conversacion, TicketProducto, PerfilCliente
from sqlalchemy.orm import joinedload
from typing import List

class SoporteResolucionRoute:
    @staticmethod
    def create(asesor_id: int, causa: str, estado: str, notas: str, conversacion_id: int = None, ticket_id: int = None, tipo_resolucion: str = 'chat'):
        existente = None
        if conversacion_id:
            existente = SoporteResolucion.query.filter_by(conversacion_id=conversacion_id).first()
        elif ticket_id:
            existente = SoporteResolucion.query.filter_by(ticket_id=ticket_id).first()
        
        if existente:
            return existente

        nueva_resolucion = SoporteResolucion(
            conversacion_id=conversacion_id,
            asesor_id=asesor_id,
            causa_problema=causa,
            estado_resolucion=estado,
            notas=notas,
            ticket_id=ticket_id,
            tipo_resolucion=tipo_resolucion
        )
        db.session.add(nueva_resolucion)
        db.session.commit()
        return nueva_resolucion
    
    @staticmethod
    def get_all() -> List[SoporteResolucion]:
        """Obtiene todas las resoluciones con sus relaciones precargadas."""
        return SoporteResolucion.query.options(
            joinedload(SoporteResolucion.asesor),
            joinedload(SoporteResolucion.conversacion).joinedload(Conversacion.perfil_cliente).joinedload(PerfilCliente.usuario),
            joinedload(SoporteResolucion.ticket).joinedload(TicketProducto.perfil_cliente).joinedload(PerfilCliente.usuario)
        ).order_by(SoporteResolucion.fecha_creacion.desc()).all()