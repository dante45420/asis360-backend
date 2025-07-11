# app/models/__init__.py

from .organizacion_model import Organizacion
from .usuario_model import Usuario
from .perfil_cliente_model import PerfilCliente
from .proveedor_model import Proveedor
from .perfil_proveedor_model import PerfilProveedor
from .producto_model import Producto
from .requisito_producto_model import RequisitoProducto
from .precios_producto_model import PreciosProducto
from .pedido_model import Pedido
from .detalle_pedido_model import DetallePedido
from .conversacion_model import Conversacion
from .mensaje_model import Mensaje
from .soporte_resolucion_model import SoporteResolucion
from .ticket_producto_model import TicketProducto
from .reseña_model import Reseña
from .disponibilidad_asesor_model import DisponibilidadAsesor
from .solicitud_asesor_model import SolicitudAsesor

print("Todos los modelos (nueva arquitectura) han sido importados.")