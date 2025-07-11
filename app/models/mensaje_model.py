# app/models/mensaje_model.py
from app import db
from datetime import datetime

class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    mensaje_id = db.Column(db.Integer, primary_key=True)
    conversacion_id = db.Column(db.Integer, db.ForeignKey('conversaciones.conversacion_id', ondelete='CASCADE'), nullable=False, index=True)
    wam_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    remitente = db.Column(db.String(20), nullable=False)
    tipo_mensaje = db.Column(db.String(50), default='text')
    cuerpo_mensaje = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)

    # --- RELACIÓN CORREGIDA ---
    conversacion = db.relationship('Conversacion', back_populates='mensajes')

    def __repr__(self):
        return f"<Mensaje {self.mensaje_id} de {self.remitente}>"