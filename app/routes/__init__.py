# app/routes/__init__.py

from .usuario_routes import UsuarioRoute
from .perfil_cliente_routes import PerfilClienteRoute
from .conversacion_routes import ConversacionRoute
from .pedido_routes import PedidoRoute
from .detalle_pedido_routes import DetallePedidoRoute
from .producto_routes import ProductoRoute
from .proveedor_routes import ProveedorRoute
from .precios_producto_routes import PreciosProductoRoute
from .requisitos_productos_routes import RequisitoProductoRoute
from .soporte_resolucion_routes import SoporteResolucionRoute
from .ticket_producto_routes import TicketProductoRoute
from .mensaje_routes import MensajeRoute
from .reseña_routes import ReseñaRoute
from .disponibilidad_asesor_routes import DisponibilidadAsesorRoute
from .solicitud_asesor_routes import SolicitudAsesorRoute
from .dashboard_routes import DashboardRoute

print("Todas las clases de rutas han sido importadas.")