# app/models/solicitud_asesor_model.py
from app import db
from datetime import datetime

class SolicitudAsesor(db.Model):
    __tablename__ = 'solicitudes_asesor'

    id = db.Column(db.Integer, primary_key=True)
    perfil_cliente_id = db.Column(db.Integer, db.ForeignKey('perfiles_cliente.perfil_cliente_id'), nullable=False)
    # AÑADIDO: Campo para registrar el asesor asignado
    asesor_asignado_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), nullable=True)
    
    metodo_contacto = db.Column(db.String(50), nullable=False)
    detalles_adicionales = db.Column(db.Text, nullable=True)
    
    estado = db.Column(db.String(50), default='pendiente', nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)

    # ELIMINADO: 'fecha_reunion_propuesta' ya no es necesario, se asocia a un horario
    # Lo vinculamos directamente al slot de disponibilidad reservado
    disponibilidad_reservada = db.relationship('DisponibilidadAsesor', backref='solicitud_asignada', uselist=False)
    perfil_cliente = db.relationship('PerfilCliente', backref='solicitudes_asesor')
    asesor_asignado = db.relationship('Usuario', foreign_keys=[asesor_asignado_id])

    def __repr__(self):
        return f"<SolicitudAsesor {self.id} de {self.perfil_cliente_id}>"