# app/models/soporte_resolucion_model.py
from app import db
from datetime import datetime

class SoporteResolucion(db.Model):
    __tablename__ = 'soporte_resoluciones'

    resolucion_id = db.Column(db.Integer, primary_key=True)
    conversacion_id = db.Column(db.Integer, db.ForeignKey('conversaciones.conversacion_id'), nullable=True, unique=True)
    # MODIFICADO: El asesor ahora es un Usuario
    asesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False)
    
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket_producto.ticket_id'), nullable=True, unique=True)
    tipo_resolucion = db.Column(db.String(50), nullable=False, default='chat')
    
    causa_problema = db.Column(db.String(255), nullable=False)
    estado_resolucion = db.Column(db.String(50), nullable=False)
    notas = db.Column(db.Text, nullable=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    conversacion = db.relationship('Conversacion', backref=db.backref('resolucion', uselist=False))
    ticket = db.relationship('TicketProducto', backref=db.backref('resolucion', uselist=False))
    # MODIFICADO: El asesor ahora es un Usuario
    asesor = db.relationship('Usuario')

    def __repr__(self):
        return f"<SoporteResolucion {self.resolucion_id} para {self.tipo_resolucion}>"