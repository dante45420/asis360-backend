# app/models/disponibilidad_asesor_model.py
from app import db
from datetime import datetime

class DisponibilidadAsesor(db.Model):
    __tablename__ = 'disponibilidad_asesor'

    id = db.Column(db.Integer, primary_key=True)
    # En el futuro, se puede vincular a un asesor específico (usuario con rol 'admin')
    asesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False)
    
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False, unique=True)
    duracion_minutos = db.Column(db.Integer, default=30)
    esta_reservado = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Podríamos añadir una relación a la solicitud que reservó este horario
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_asesor.id'), nullable=True)

    def __repr__(self):
        return f"<Disponibilidad {self.id} - {self.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M')}>"