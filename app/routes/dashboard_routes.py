# app/routes/dashboard_routes.py
from app import db
from app.models import Pedido, DetallePedido, PerfilCliente, Mensaje, Usuario
# IMPORTACIÓN CORREGIDA: Se añade 'cast'
from sqlalchemy import func, distinct, cast
from datetime import datetime, timedelta
import decimal

class DashboardRoute:

    @staticmethod
    def get_system_health():
        try:
            db.session.query(func.now()).first()
            db_status = 'Online'
        except Exception:
            db_status = 'Offline'
            
        last_message = Mensaje.query.order_by(Mensaje.fecha_envio.desc()).first()
        last_webhook_time = last_message.fecha_envio.isoformat() if last_message else None

        whatsapp_api_status = 'Operacional'
        background_task_status = 'Activa'

        return {
            "database_status": db_status,
            "whatsapp_api_status": whatsapp_api_status,
            "background_task_status": background_task_status,
            "last_webhook_received": last_webhook_time
        }

    @staticmethod
    def get_business_kpis():
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # 1. Total de Ventas (pedidos completados)
        total_sales_query = db.session.query(func.sum(Pedido.monto_total)).filter(Pedido.estado == 'completo').scalar()
        total_sales = total_sales_query or decimal.Decimal('0.0')

        # 2. Ahorro Total para Clientes
        # La función 'cast' ahora está importada y funcionará correctamente.
        total_saved_query = db.session.query(
            func.sum((DetallePedido.precio_unitario_historico - DetallePedido.precio_pagado) * cast(DetallePedido.respuestas_requisitos['Cantidad'].astext, db.Integer))
        ).join(Pedido).filter(
            Pedido.estado == 'completo',
            DetallePedido.precio_pagado < DetallePedido.precio_unitario_historico
        ).scalar()
        total_saved = total_saved_query or decimal.Decimal('0.0')

        # 3. Nuevos Clientes (últimos 30 días) - *** LÓGICA CORREGIDA ***
        # Ahora filtra directamente sobre el nuevo campo 'fecha_registro' en PerfilCliente.
        new_clients_count = db.session.query(func.count(PerfilCliente.perfil_cliente_id))\
            .filter(PerfilCliente.fecha_registro >= thirty_days_ago)\
            .scalar()

        # 4. Clientes Activos (han creado un pedido en los últimos 30 días)
        active_clients_count = db.session.query(func.count(distinct(Pedido.perfil_cliente_id))).filter(
            Pedido.fecha_creacion >= thirty_days_ago
        ).scalar()

        # 5. Pedidos Totales (excluyendo carritos pendientes)
        total_orders_count = db.session.query(func.count(Pedido.pedido_id)).filter(Pedido.estado != 'pendiente').scalar()

        return {
            "total_sales": float(total_sales),
            "total_saved_for_clients": float(total_saved),
            "new_clients_last_30_days": new_clients_count,
            "active_clients_last_30_days": active_clients_count,
            "total_orders": total_orders_count
        }