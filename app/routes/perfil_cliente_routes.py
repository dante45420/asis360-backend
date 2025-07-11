# app/routes/perfil_cliente_routes.py
from app import db
from app.models import PerfilCliente
from app.models import Pedido, TicketProducto, SolicitudAsesor, Proveedor, Producto, DetallePedido
from typing import Optional
from sqlalchemy import func, distinct
import decimal

class PerfilClienteRoute:
    @staticmethod
    def get_by_phone(phone_number: str) -> Optional[PerfilCliente]:
        return PerfilCliente.query.filter_by(telefono_vinculado=phone_number).first()

    @staticmethod
    def create(phone_number: str, usuario_id: int = None, organizacion_id: int = None, nombre: str = None) -> PerfilCliente:
        """
        Crea un nuevo PerfilCliente.
        Ahora acepta un nombre opcional.
        """
        nuevo_perfil = PerfilCliente(
            telefono_vinculado=phone_number,
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
            nombre=nombre # <-- Parámetro añadido
        )
        db.session.add(nuevo_perfil)
        db.session.commit()
        return nuevo_perfil

    @staticmethod
    def update_by_id(perfil_id: int, data: dict) -> Optional[PerfilCliente]:
        """Actualiza un perfil de cliente con nuevos datos."""
        perfil = PerfilCliente.query.get(perfil_id)
        if perfil:
            for key, value in data.items():
                if hasattr(perfil, key):
                    setattr(perfil, key, value)
            db.session.commit()
        return perfil
    
    # --- NUEVO MÉTODO PARA ESTADÍSTICAS ---
    @staticmethod
    def get_dashboard_stats(perfil_cliente_id: int) -> dict:
        """
        Calcula y devuelve un diccionario con estadísticas para el panel del cliente,
        usando la nueva lógica de ahorro.
        """
        
        # Lógicas para pedidos_exitosos, proveedores_unicos y tickets_soporte se mantienen igual.
        pedidos_exitosos = db.session.query(func.count(Pedido.pedido_id)).filter(
            Pedido.perfil_cliente_id == perfil_cliente_id,
            Pedido.estado == 'completo'
        ).scalar()

        proveedores_unicos = db.session.query(func.count(distinct(Producto.proveedor_id)))\
            .join(DetallePedido, DetallePedido.producto_id == Producto.producto_id)\
            .join(Pedido, Pedido.pedido_id == DetallePedido.pedido_id)\
            .filter(
                Pedido.perfil_cliente_id == perfil_cliente_id,
                Pedido.estado == 'completo'
            ).scalar()

        tickets_soporte = db.session.query(func.count(TicketProducto.ticket_id)).filter_by(
            perfil_cliente_id=perfil_cliente_id
        ).scalar()

        # --- LÓGICA DE CÁLCULO DE AHORRO ACTUALIZADA ---
        total_ahorrado = decimal.Decimal('0.0')
        
        # Buscamos todos los detalles de pedidos completados para el cliente
        detalles_de_pedidos_completos = db.session.query(DetallePedido)\
            .join(Pedido)\
            .filter(Pedido.perfil_cliente_id == perfil_cliente_id, Pedido.estado == 'completo')\
            .all()

        for detalle in detalles_de_pedidos_completos:
            # Nos aseguramos de que ambos precios existan para la comparación
            if detalle.precio_unitario_historico and detalle.precio_pagado:
                # El ahorro solo se cuenta si el precio pagado fue menor al de referencia
                if detalle.precio_unitario_historico > detalle.precio_pagado:
                    cantidad = int(detalle.respuestas_requisitos.get('Cantidad', 1))
                    # El ahorro es la diferencia entre el precio original y el final, por la cantidad
                    ahorro_por_item = (detalle.precio_unitario_historico - detalle.precio_pagado) * cantidad
                    total_ahorrado += ahorro_por_item
        # --- FIN DE LA LÓGICA ---

        return {
            "pedidos_exitosos": pedidos_exitosos,
            "proveedores_unicos": proveedores_unicos,
            "tickets_soporte": tickets_soporte,
            "dinero_ahorrado": float(total_ahorrado)
        }
    
    @staticmethod
    def get_all_paginated(page: int, per_page: int):
        """Devuelve una lista paginada de todos los perfiles de cliente."""
        return PerfilCliente.query.order_by(PerfilCliente.nombre.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # --- MÉTODO MODIFICADO (para búsqueda) ---
    @staticmethod
    def search_by_query(query: str, page: int, per_page: int):
        """Busca perfiles por nombre o teléfono con paginación."""
        search_term = f"%{query}%"
        return PerfilCliente.query.filter(
            db.or_(
                PerfilCliente.nombre.ilike(search_term),
                PerfilCliente.telefono_vinculado.ilike(search_term)
            )
        ).order_by(PerfilCliente.nombre.asc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def update_bot_status(perfil_id: int, status: bool):
        """Actualiza el estado de pausa del bot para un perfil."""
        perfil = PerfilCliente.query.get(perfil_id)
        if perfil:
            perfil.bot_pausado = status
        # El commit se hace en la API
    
    @staticmethod
    def get_by_id(perfil_id: int) -> Optional[PerfilCliente]:
        """Obtiene un perfil de cliente por su ID."""
        return PerfilCliente.query.get(perfil_id)