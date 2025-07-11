# app/models/conversacion_model.py
from app import db
from datetime import datetime

class Conversacion(db.Model):
    __tablename__ = 'conversaciones'
    
    conversacion_id = db.Column(db.Integer, primary_key=True)
    perfil_cliente_id = db.Column(db.Integer, db.ForeignKey('perfiles_cliente.perfil_cliente_id'), nullable=False)
    asesor_asignado_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), nullable=True)
    
    fecha_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estado_actual = db.Column(db.String(100), default='inicio')
    estado_soporte = db.Column(db.String(50), default='inactiva', nullable=False, index=True)

    # --- RELACIONES CORREGIDAS ---
    perfil_cliente = db.relationship('PerfilCliente', back_populates='conversaciones')
    asesor_asignado = db.relationship('Usuario') # Esta es una relación simple de un solo lado
    mensajes = db.relationship('Mensaje', back_populates='conversacion', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversacion {self.conversacion_id}>"