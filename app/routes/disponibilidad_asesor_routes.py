from app import db
from app.models import DisponibilidadAsesor, SolicitudAsesor, PerfilCliente
from sqlalchemy.orm import joinedload # <-- IMPORTACIÓN AÑADIDA
from typing import List
from datetime import datetime


class DisponibilidadAsesorRoute:
    @staticmethod
    def create(fecha_hora_inicio: datetime, asesor_id: int) -> DisponibilidadAsesor:
        """Crea un nuevo horario de disponibilidad para un asesor específico."""
        nueva_disponibilidad = DisponibilidadAsesor(
            fecha_hora_inicio=fecha_hora_inicio,
            asesor_id=asesor_id
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return nueva_disponibilidad

    @staticmethod
    def get_by_asesor_id(asesor_id: int) -> List[DisponibilidadAsesor]:
        """Obtiene todos los horarios (reservados y no) para un asesor específico."""
        return DisponibilidadAsesor.query.filter_by(asesor_id=asesor_id)\
            .order_by(DisponibilidadAsesor.fecha_hora_inicio.asc()).all()
    
    @staticmethod
    def get_all_available() -> List[DisponibilidadAsesor]:
        """Obtiene solo los horarios disponibles y futuros de TODOS los asesores."""
        return DisponibilidadAsesor.query.filter(
            DisponibilidadAsesor.esta_reservado == False,
            DisponibilidadAsesor.fecha_hora_inicio > datetime.utcnow()
        ).order_by(DisponibilidadAsesor.fecha_hora_inicio.asc()).all()

    @staticmethod
    def get_by_id(slot_id: int) -> DisponibilidadAsesor:
        """Obtiene un slot específico por su ID."""
        return DisponibilidadAsesor.query.get(slot_id)

    @staticmethod
    def delete(disponibilidad_id: int) -> bool:
        """Elimina un horario, solo si no está reservado."""
        slot = DisponibilidadAsesor.query.get(disponibilidad_id)
        if slot and not slot.esta_reservado:
            db.session.delete(slot)
            db.session.commit()
            return True
        return False

    @staticmethod
    def reserve(disponibilidad_id: int, solicitud_id: int) -> bool:
        """Marca un horario como reservado y lo vincula a una solicitud."""
        slot = DisponibilidadAsesor.query.get(disponibilidad_id)
        if slot and not slot.esta_reservado:
            slot.esta_reservado = True
            slot.solicitud_id = solicitud_id
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_reserved_by_asesor_id(asesor_id: int) -> List[DisponibilidadAsesor]:
        """Obtiene los horarios reservados de un asesor, con datos del cliente."""
        return DisponibilidadAsesor.query.options(
            joinedload(DisponibilidadAsesor.solicitud_asignada)
            .joinedload(SolicitudAsesor.perfil_cliente)
        ).filter(
            DisponibilidadAsesor.asesor_id == asesor_id,
            DisponibilidadAsesor.esta_reservado == True
        ).order_by(DisponibilidadAsesor.fecha_hora_inicio.asc()).all()