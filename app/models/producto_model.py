from app import db

class Producto(db.Model):
    __tablename__ = 'productos'
    producto_id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.proveedor_id'), nullable=False)
    nombre_producto = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(50), unique=True)
    categoria = db.Column(db.String(100), index=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    media_url = db.Column(db.Text, nullable=True)
    media_type = db.Column(db.String(20), nullable=True)

    requisitos = db.relationship('RequisitoProducto', backref='producto', lazy=True, cascade="all, delete-orphan")
    precios = db.relationship('PreciosProducto', backref='producto', lazy=True, cascade="all, delete-orphan")
    detalles_pedido = db.relationship('DetallePedido', back_populates='producto')