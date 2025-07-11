# app/models/perfil_cliente_model.py
# app/models/perfil_cliente_model.py
from app import db

class PerfilCliente(db.Model):
    __tablename__ = 'perfiles_cliente'

    perfil_cliente_id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.usuario_id'), unique=True, nullable=True)
    organizacion_id = db.Column(db.Integer, db.ForeignKey('organizaciones.organizacion_id'), nullable=True)
    
    nombre = db.Column(db.String(100), nullable=True)
    nombre_pendiente = db.Column(db.String(100), nullable=True)
    telefono_vinculado = db.Column(db.String(20), unique=True, nullable=False)
    rut = db.Column(db.String(12), unique=True, nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    bot_pausado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_registro = db.Column(db.TIMESTAMP, server_default=db.func.now())
    codigo_verificacion = db.Column(db.String(6), nullable=True)
    codigo_expiracion = db.Column(db.DateTime, nullable=True)

    # --- RELACIONES CORREGIDAS ---
    usuario = db.relationship('Usuario', back_populates='perfil_cliente')
    pedidos = db.relationship('Pedido', back_populates='perfil_cliente', lazy='dynamic')
    conversaciones = db.relationship('Conversacion', back_populates='perfil_cliente', lazy='dynamic')
    tickets_producto = db.relationship('TicketProducto', back_populates='perfil_cliente', lazy='dynamic')

    def __repr__(self):
        return f"<PerfilCliente {self.perfil_cliente_id}>"