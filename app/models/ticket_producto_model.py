# app/models/ticket_producto_model.py
from app import db

class TicketProducto(db.Model):
    __tablename__ = 'ticket_producto'

    ticket_id = db.Column(db.Integer, primary_key=True)
    # MODIFICADO: Ahora se relaciona con PerfilCliente
    perfil_cliente_id = db.Column(db.Integer, db.ForeignKey('perfiles_cliente.perfil_cliente_id'), nullable=False)
    
    fecha_creacion = db.Column(db.TIMESTAMP, server_default=db.func.now())
    nombre_producto_deseado = db.Column(db.String(200), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(50), default='incompleto')

    perfil_cliente = db.relationship('PerfilCliente', back_populates='tickets_producto')

    def __repr__(self):
        return f"<TicketProducto {self.ticket_id} - PerfilCliente {self.perfil_cliente_id}>"