# app/routes/conversacion_routes.py
from app import db
from app.models import Conversacion, Mensaje
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

class ConversacionRoute:
    @staticmethod
    def get_active_conversation(perfil_cliente_id: int) -> Optional[Conversacion]:
        """Busca una conversación activa para un PerfilCliente."""
        return Conversacion.query.filter(
            Conversacion.perfil_cliente_id == perfil_cliente_id,
            Conversacion.fecha_fin.is_(None)
        ).first()

    @staticmethod
    def create_new_conversation(perfil_cliente_id: int) -> Conversacion:
        """Crea una nueva conversación con el estado inicial 'inicio'."""
        nueva_conversacion = Conversacion(
            perfil_cliente_id=perfil_cliente_id,
            estado_actual='inicio', # El estado inicial es siempre 'inicio'
            estado_soporte='inactiva'
        )
        db.session.add(nueva_conversacion)
        db.session.commit()
        return nueva_conversacion

    @staticmethod
    def get_by_id(conversacion_id: int) -> Optional[Conversacion]:
        return Conversacion.query.get(conversacion_id)

    @staticmethod
    def update_conversation_state(conversacion_id: int, nuevo_estado: str):
        conversacion = Conversacion.query.get(conversacion_id)
        if conversacion:
            conversacion.estado_actual = nuevo_estado
            db.session.commit()

    @staticmethod
    def update_support_state(conversacion_id: int, nuevo_estado_soporte: str):
        conversacion = Conversacion.query.get(conversacion_id)
        if conversacion:
            conversacion.estado_soporte = nuevo_estado_soporte
            db.session.commit()

    @staticmethod
    def get_support_chats(estado: str) -> List[Conversacion]:
        return Conversacion.query.filter(Conversacion.estado_soporte == estado).order_by(Conversacion.fecha_inicio.desc()).all()

    @staticmethod
    def assign_asesor(conversacion_id: int, asesor_id: int) -> Optional[Conversacion]:
        """Asigna un asesor (usuario_id) y cambia el estado a 'activa'."""
        conversacion = Conversacion.query.get(conversacion_id)
        if conversacion and conversacion.estado_soporte == 'pendiente':
            conversacion.asesor_asignado_id = asesor_id
            conversacion.estado_soporte = 'activa'
            db.session.commit()
            return conversacion
        return None
    
    @staticmethod
    def finalize_support_conversation(conversacion_id: int) -> Optional[Conversacion]:
        """
        CORREGIDO: Marca una conversación de soporte como 'resuelta' y establece la fecha de fin.
        Ahora actualiza el campo correcto 'estado_soporte'.
        """
        conversacion = Conversacion.query.get(conversacion_id)
        if conversacion and not conversacion.fecha_fin:
            conversacion.estado_soporte = 'resuelta' # <--- CAMBIO CLAVE
            conversacion.fecha_fin = datetime.utcnow()
            db.session.commit()
            return conversacion
        return None
    
    @staticmethod
    def finalize_conversation(conversacion_id: int, final_state: str) -> Optional[Conversacion]:
        """Función única para finalizar una conversación."""
        conversacion = Conversacion.query.get(conversacion_id)
        if conversacion and not conversacion.fecha_fin:
            conversacion.estado_actual = final_state
            conversacion.fecha_fin = datetime.utcnow()
            db.session.commit()
            return conversacion
        return None

    @staticmethod
    def end_inactive_conversations(timeout_minutes: int) -> List[Conversacion]:
        """Busca y finaliza conversaciones inactivas basándose en el último mensaje."""
        timeout_delta = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        last_message_subquery = db.session.query(
            Mensaje.conversacion_id,
            func.max(Mensaje.fecha_envio).label('last_message_time')
        ).group_by(Mensaje.conversacion_id).subquery()
        conversaciones_a_cerrar = db.session.query(Conversacion).join(
            last_message_subquery,
            Conversacion.conversacion_id == last_message_subquery.c.conversacion_id
        ).filter(
            Conversacion.fecha_fin.is_(None),
            Conversacion.estado_soporte == 'inactiva',
            last_message_subquery.c.last_message_time < timeout_delta
        ).all()
        if not conversaciones_a_cerrar:
            return []
        for conv in conversaciones_a_cerrar:
            ConversacionRoute.finalize_conversation(conv.conversacion_id, 'expirada')
        return conversaciones_a_cerrar
    
    @staticmethod
    def create_with_initial_state(perfil_cliente_id: int, initial_state: str):
        """
        Crea una nueva conversación para un PerfilCliente con un estado inicial específico.
        """
        from app.models import Conversacion
        from app import db
        
        nueva_conversacion = Conversacion(
            perfil_cliente_id=perfil_cliente_id,
            estado_actual=initial_state,
            estado_soporte='inactiva'
        )
        db.session.add(nueva_conversacion)
        db.session.commit()
        return nueva_conversacion