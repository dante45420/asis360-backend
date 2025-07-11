# app/routes/mensaje_routes.py
from app import db
from app.models.mensaje_model import Mensaje
from typing import Optional, List

class MensajeRoute:
    """
    Gestiona las operaciones de la base de datos para la entidad Mensaje.
    """

    @staticmethod
    def registrar_mensaje_usuario(conversacion_id: int, wam_id: str, tipo_mensaje: str, cuerpo_mensaje: str):
        nuevo_mensaje = Mensaje(
            conversacion_id=conversacion_id,
            wam_id=wam_id,
            tipo_mensaje=tipo_mensaje,
            cuerpo_mensaje=cuerpo_mensaje,
            remitente='usuario'
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()
        return nuevo_mensaje

    @staticmethod
    def get_messages_for_conversation(conversacion_id: int, limit: int = 50) -> List[Mensaje]:
        return Mensaje.query.filter_by(conversacion_id=conversacion_id).order_by(Mensaje.fecha_envio.desc()).limit(limit).all()

    @staticmethod
    def wam_id_exists(wam_id: str) -> bool:
        return Mensaje.query.filter_by(wam_id=wam_id).first() is not None

    @staticmethod
    def create_asesor_message(conversacion_id: int, texto: str, asesor_id: int):
        nuevo_mensaje = Mensaje(
            conversacion_id=conversacion_id,
            remitente='asesor',
            tipo_mensaje='text',
            cuerpo_mensaje=texto
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()
        return nuevo_mensaje
    
    # --- FUNCIÓN AÑADIDA ---
    @staticmethod
    def create_bot_message(conversacion_id: int, texto: str):
        """Crea un registro de mensaje enviado por el bot."""
        nuevo_mensaje = Mensaje(
            conversacion_id=conversacion_id,
            remitente='bot',
            tipo_mensaje='text',
            cuerpo_mensaje=texto
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()
        return nuevo_mensaje