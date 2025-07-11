# app/api/admin_api_routes.py

from flask import Blueprint, jsonify, request, current_app
from app.api.auth_utils import admin_required

# Importación de las nuevas rutas refactorizadas
from app.routes import (
    PedidoRoute, ProveedorRoute, ProductoRoute, PreciosProductoRoute,
    RequisitoProductoRoute, ConversacionRoute, MensajeRoute, TicketProductoRoute,
    SoporteResolucionRoute, PerfilClienteRoute, DisponibilidadAsesorRoute, DetallePedidoRoute,
    DashboardRoute,
)

from app.models import Pedido, DetallePedido, PerfilCliente, Producto # Importa los modelos necesarios
# Importación de Servicios
from app.services import s3_service
from app.services.whatsapp_api_client import WhatsAppApiClient
from app.services.whatsapp_message_builder import WhatsappMessageBuilder
from app import db
import decimal
from datetime import datetime, time, timedelta

bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# --- ENDPOINTS DE PEDIDOS ---

@bp.route('/pedidos', methods=['GET', 'OPTIONS'])
@admin_required
def obtener_pedidos(current_user):
    estado = request.args.get('estado')
    
    try:
        pedidos_data = PedidoRoute.get_orders_by_status(estado)

        if estado == 'en_espera':
            # Para 'en_espera', la data ya es un JSON, se devuelve directamente.
            return jsonify(pedidos_data)
        
        # Para otros estados, procesamos la lista de objetos Pedido.
        pedidos_list = []
        for p in pedidos_data:
            try:
                # --- LÓGICA DE ROBUSTEZ AÑADIDA ---
                # Intentamos serializar cada pedido individualmente.
                nombre_cliente = "N/A"
                if p.perfil_cliente:
                    nombre_cliente = (p.perfil_cliente.usuario.nombre if p.perfil_cliente.usuario 
                                      else p.perfil_cliente.nombre or p.perfil_cliente.telefono_vinculado)
                
                pedidos_list.append({
                    "pedido_id": p.pedido_id,
                    "cliente_nombre": nombre_cliente,
                    "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
                    "estado": p.estado,
                    "monto_total": float(p.monto_total) if p.monto_total is not None else 0,
                    "tiene_comprobante": True if p.path_comprobante else False
                })
            except Exception as e:
                # Si un pedido falla, lo registramos en la consola y continuamos con los demás.
                current_app.logger.error(f"Error al procesar el pedido ID {p.pedido_id}: {e}")
                continue # Salta al siguiente pedido en el bucle
        
        return jsonify(pedidos_list)

    except Exception as e:
        current_app.logger.error(f"Error crítico al obtener pedidos con estado '{estado}': {e}")
        traceback.print_exc()
        return jsonify({"message": f"Error al obtener pedidos. Revisa la consola del servidor."}), 500



@bp.route('/pedidos/<int:pedido_id>/aprobar', methods=['POST'])
@admin_required
def aprobar_pago_pedido(current_user, pedido_id):
    pedido = PedidoRoute.get_pedido_by_id(pedido_id)
    if not pedido or pedido.estado != 'en_revision':
        return jsonify({"message": "Pedido no válido para aprobación."}), 400
    
    PedidoRoute.update_order_state(pedido_id, 'pagado')
    
    try:
        if pedido.perfil_cliente and pedido.perfil_cliente.telefono_vinculado:
            msg = WhatsappMessageBuilder.get_payment_approved_message(pedido.pedido_id)
            WhatsAppApiClient.send_message(pedido.perfil_cliente.telefono_vinculado, msg)
    except Exception as e:
        print(f"ERROR al notificar al cliente sobre aprobación: {e}")
        
    return jsonify({"message": f"Pedido #{pedido_id} aprobado exitosamente."})

@bp.route('/pedidos/<int:pedido_id>/rechazar', methods=['POST'])
@admin_required
def rechazar_pago_pedido(current_user, pedido_id):
    data = request.get_json()
    motivo = data.get('motivo')
    pedido = PedidoRoute.get_pedido_by_id(pedido_id)
    if not pedido or pedido.estado != 'en_revision':
        return jsonify({"message": "Pedido no válido para rechazo."}), 400
    
    PedidoRoute.update_order_state(pedido_id, 'esperando_pago')
    
    try:
        if pedido.perfil_cliente and pedido.perfil_cliente.telefono_vinculado:
            msg = WhatsappMessageBuilder.get_payment_rejected_message(motivo)
            WhatsAppApiClient.send_message(pedido.perfil_cliente.telefono_vinculado, msg)
    except Exception as e:
        print(f"ERROR al notificar al cliente sobre rechazo: {e}")

    return jsonify({"message": f"Pedido #{pedido_id} rechazado. Se ha notificado al cliente."})

@bp.route('/pedidos/<int:pedido_id>/comprobante_url', methods=['GET'])
@admin_required
def get_comprobante_url(current_user, pedido_id):
    pedido = PedidoRoute.get_pedido_by_id(pedido_id)
    if not pedido or not pedido.path_comprobante:
        return jsonify({"message": "Comprobante no encontrado"}), 404
    
    bucket_name = current_app.config['S3_BUCKET_NAME']
    presigned_url = s3_service.generate_presigned_url(bucket_name, pedido.path_comprobante)
    
    if not presigned_url:
        return jsonify({"message": "No se pudo generar la URL"}), 500
        
    return jsonify({"url": presigned_url})


# --- ENDPOINTS CRUD PARA PROVEEDORES ---

@bp.route('/proveedores', methods=['GET'])
@admin_required
def get_proveedores(current_user):
    proveedores = ProveedorRoute.get_all()
    proveedores_data = [{"proveedor_id": p.proveedor_id, "nombre": p.nombre, "info_contacto": p.info_contacto, "calidad_servicio": p.calidad_servicio} for p in proveedores]
    return jsonify(proveedores_data)

@bp.route('/proveedores', methods=['POST'])
@admin_required
def create_proveedor(current_user):
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify({"message": "El campo 'nombre' es requerido"}), 400
    nuevo_proveedor = ProveedorRoute.create(data)
    return jsonify({"message": "Proveedor creado exitosamente", "proveedor_id": nuevo_proveedor.proveedor_id}), 201

@bp.route('/proveedores/<int:proveedor_id>', methods=['PUT'])
@admin_required
def update_proveedor(current_user, proveedor_id):
    data = request.get_json()
    proveedor_actualizado = ProveedorRoute.update(proveedor_id, data)
    if proveedor_actualizado:
        return jsonify({"message": "Proveedor actualizado exitosamente"})
    return jsonify({"message": "Proveedor no encontrado"}), 404

@bp.route('/proveedores/<int:proveedor_id>', methods=['DELETE'])
@admin_required
def delete_proveedor(current_user, proveedor_id):
    if ProveedorRoute.delete(proveedor_id):
        return jsonify({"message": "Proveedor eliminado exitosamente"})
    return jsonify({"message": "Proveedor no encontrado"}), 404


# --- ENDPOINTS CRUD PARA PRODUCTOS ---

@bp.route('/productos', methods=['GET'])
@admin_required
def get_productos(current_user):
    productos = ProductoRoute.get_all_for_admin()
    return jsonify([{
        "producto_id": p.producto_id,
        "nombre_producto": p.nombre_producto,
        "sku": p.sku,
        "categoria": p.categoria,
        "proveedor_nombre": p.proveedor.nombre if p.proveedor else "N/A",
        "proveedor_id": p.proveedor_id
    } for p in productos])

@bp.route('/productos', methods=['POST'])
@admin_required
def create_producto(current_user):
    data = request.get_json()
    if not data or not data.get('nombre_producto') or not data.get('proveedor_id'):
        return jsonify({"message": "Nombre del producto y proveedor son requeridos"}), 400
    nuevo_producto = ProductoRoute.create(data)
    return jsonify({"message": "Producto creado exitosamente", "producto": {"producto_id": nuevo_producto.producto_id, "nombre_producto": nuevo_producto.nombre_producto}}), 201

@bp.route('/productos/<int:producto_id>', methods=['PUT'])
@admin_required
def update_producto(current_user, producto_id):
    data = request.get_json()
    try:
        producto_actualizado = ProductoRoute.update(producto_id, data)
        if producto_actualizado:
            return jsonify({"message": "Producto actualizado exitosamente"})
        return jsonify({"message": "Producto no encontrado"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@bp.route('/productos/<int:producto_id>', methods=['DELETE'])
@admin_required
def delete_producto(current_user, producto_id):
    if ProductoRoute.soft_delete(producto_id):
        return jsonify({"message": "Producto eliminado exitosamente"})
    return jsonify({"message": "Producto no encontrado"}), 404

@bp.route('/productos/<int:producto_id>/details', methods=['GET'])
@admin_required
def get_producto_details(current_user, producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return jsonify({
        "producto_id": producto.producto_id, "nombre_producto": producto.nombre_producto, "sku": producto.sku, "categoria": producto.categoria,
        "precios": [{"precio_id": p.precio_id, "variante_requisitos": p.variante_requisitos, "cantidad_minima": p.cantidad_minima, "precio_unitario": float(p.precio_unitario) } for p in producto.precios],
        "requisitos": [{"requisito_id": r.requisito_id, "nombre_requisito": r.nombre_requisito, "orden": r.orden, "opciones": r.opciones } for r in producto.requisitos]
    })


# --- ENDPOINTS PARA PRECIOS Y REQUISITOS ---

@bp.route('/productos/precios', methods=['POST'])
@admin_required
def create_precio_producto(current_user):
    data = request.get_json()
    nuevo_precio = PreciosProductoRoute.create(data)
    return jsonify({"message": "Precio creado exitosamente", "precio_id": nuevo_precio.precio_id}), 201

@bp.route('/productos/precios/<int:precio_id>', methods=['DELETE'])
@admin_required
def delete_precio_producto(current_user, precio_id):
    if PreciosProductoRoute.delete(precio_id):
        return jsonify({"message": "Precio eliminado exitosamente"})
    return jsonify({"message": "Precio no encontrado"}), 404

@bp.route('/productos/requisitos', methods=['POST'])
@admin_required
def create_requisito_producto(current_user):
    data = request.get_json()
    nuevo_req = RequisitoProductoRoute.create(data)
    return jsonify({"message": "Requisito creado exitosamente", "requisito_id": nuevo_req.requisito_id}), 201

@bp.route('/productos/requisitos/<int:requisito_id>', methods=['DELETE'])
@admin_required
def delete_requisito_producto(current_user, requisito_id):
    if RequisitoProductoRoute.delete(requisito_id):
        return jsonify({"message": "Requisito eliminado exitosamente"})
    return jsonify({"message": "Requisito no encontrado"}), 404

@bp.route('/productos/precios/<int:precio_id>', methods=['PUT'])
@admin_required
def update_precio_producto(current_user, precio_id):
    data = request.get_json()
    if PreciosProductoRoute.update(precio_id, data):
        return jsonify({"message": "Precio actualizado exitosamente"})
    return jsonify({"message": "Precio no encontrado"}), 404

@bp.route('/productos/requisitos/<int:requisito_id>', methods=['PUT'])
@admin_required
def update_requisito_producto(current_user, requisito_id):
    data = request.get_json()
    if RequisitoProductoRoute.update(requisito_id, data):
        return jsonify({"message": "Requisito actualizado exitosamente"})
    return jsonify({"message": "Requisito no encontrado"}), 404


# --- ENDPOINTS PARA SOPORTE Y TICKETS (Refactorizados) ---

@bp.route('/soporte/tickets', methods=['GET'])
@admin_required
def get_tickets_producto(current_user):
    estados = request.args.get('estados', 'nuevo,en_revision').split(',')
    tickets = TicketProductoRoute.get_by_status(estados)
    tickets_data = []
    for t in tickets:
        nombre_cliente = "N/A"
        if t.perfil_cliente:
            nombre_cliente = (t.perfil_cliente.usuario.nombre if t.perfil_cliente.usuario 
                              else t.perfil_cliente.nombre or t.perfil_cliente.telefono_vinculado)
        tickets_data.append({
            "ticket_id": t.ticket_id, "fecha_creacion": t.fecha_creacion.isoformat(), "cliente_nombre": nombre_cliente,
            "nombre_producto_deseado": t.nombre_producto_deseado, "descripcion": t.descripcion, "estado": t.estado
        })
    return jsonify(tickets_data)

@bp.route('/soporte/tickets/<int:ticket_id>/estado', methods=['PUT'])
@admin_required
def update_ticket_estado(current_user, ticket_id):
    data = request.get_json()
    nuevo_estado = data.get('estado')
    if not nuevo_estado: return jsonify({"message": "El nuevo estado es requerido"}), 400

    ticket = TicketProductoRoute.update(ticket_id, {"estado": nuevo_estado})
    if not ticket: return jsonify({"message": "Ticket no encontrado"}), 404
        
    if nuevo_estado == 'completo':
        SoporteResolucionRoute.create(
            asesor_id=current_user.usuario_id, ticket_id=ticket_id, tipo_resolucion='ticket',
            causa=data.get('causa_problema'), estado='exitoso', notas=data.get('notas')
        )

    try:
        if ticket.perfil_cliente and ticket.perfil_cliente.telefono_vinculado:
            msg = WhatsappMessageBuilder.get_ticket_status_update_message(ticket.nombre_producto_deseado, nuevo_estado)
            WhatsAppApiClient.send_message(ticket.perfil_cliente.telefono_vinculado, msg)
    except Exception as e:
        print(f"Error al notificar al cliente sobre ticket: {e}")

    return jsonify({"message": f"Ticket #{ticket_id} actualizado a '{nuevo_estado}'."})

@bp.route('/soporte/chats', methods=['GET'])
@admin_required
def get_soporte_chats(current_user):
    estado = request.args.get('estado', 'pendiente')
    chats = ConversacionRoute.get_support_chats(estado)
    chats_data = []
    for c in chats:
        nombre_cliente = "N/A"
        if c.perfil_cliente:
            nombre_cliente = (c.perfil_cliente.usuario.nombre if c.perfil_cliente.usuario 
                              else c.perfil_cliente.nombre or c.perfil_cliente.telefono_vinculado)
        chats_data.append({
            "conversacion_id": c.conversacion_id, "cliente_nombre": nombre_cliente,
            "fecha_inicio": c.fecha_inicio.isoformat(), "estado_soporte": c.estado_soporte
        })
    return jsonify(chats_data)

@bp.route('/soporte/chats/<int:conversacion_id>/asignar', methods=['POST'])
@admin_required
def asignar_chat_soporte(current_user, conversacion_id):
    chat_asignado = ConversacionRoute.assign_asesor(conversacion_id, current_user.usuario_id)
    if chat_asignado:
        return jsonify({"message": "Chat asignado exitosamente"})
    return jsonify({"message": "El chat ya no está disponible"}), 400

@bp.route('/soporte/chats/<int:conversacion_id>/mensajes', methods=['GET'])
@admin_required
def get_mensajes_soporte(current_user, conversacion_id):
    limite = request.args.get('limit', 200, type=int)
    mensajes = MensajeRoute.get_messages_for_conversation(conversacion_id, limite)
    mensajes_data = [{
        "mensaje_id": m.mensaje_id, "cuerpo_mensaje": m.cuerpo_mensaje,
        "fecha_envio": m.fecha_envio.isoformat(), "remitente": m.remitente
    } for m in mensajes]
    return jsonify(mensajes_data)

@bp.route('/soporte/chats/<int:conversacion_id>/enviar_mensaje', methods=['POST'])
@admin_required
def enviar_mensaje_asesor(current_user, conversacion_id):
    """Un asesor envía un mensaje a un chat de soporte."""
    data = request.get_json()
    mensaje_texto = data.get('texto')

    if not mensaje_texto:
        return jsonify({"message": "El texto del mensaje no puede estar vacío."}), 400

    conversacion = ConversacionRoute.get_by_id(conversacion_id)
    if not conversacion or not conversacion.perfil_cliente:
        return jsonify({"message": "Conversación no encontrada."}), 404

    try:
        # Paso 1: Guardar el mensaje del asesor en la base de datos
        MensajeRoute.create_asesor_message(
            conversacion_id=conversacion_id,
            texto=mensaje_texto,
            asesor_id=current_user.usuario_id
        )

        # Paso 2: Construir el paquete del mensaje
        message_payload = WhatsappMessageBuilder.build_text_message(
            conversacion.perfil_cliente.telefono_vinculado,
            mensaje_texto
        )
        
        # Paso 3: Enviar el paquete usando el cliente de la API
        WhatsAppApiClient.send_message(message_payload)

        return jsonify({"message": "Mensaje enviado exitosamente."}), 200
        
    except Exception as e:
        return jsonify({"message": "Error interno del servidor al enviar el mensaje."}), 500


@bp.route('/soporte/chats/<int:conversacion_id>/resolver', methods=['POST'])
@admin_required
def resolver_conversacion_soporte(current_user, conversacion_id):
    data = request.get_json()
    if not all(k in data for k in ['causa_problema', 'estado_resolucion']):
        return jsonify({"message": "Faltan datos para la resolución del chat."}), 400

    SoporteResolucionRoute.create(
        conversacion_id=conversacion_id, asesor_id=current_user.usuario_id,
        causa=data['causa_problema'], estado=data['estado_resolucion'], notas=data.get('notas')
    )
    conversacion = ConversacionRoute.finalize_support_conversation(conversacion_id)
    try:
        if conversacion and conversacion.perfil_cliente:
            message_payload = WhatsappMessageBuilder.build_support_session_ended_message(
                conversacion.perfil_cliente.telefono_vinculado
            )
            # 2. Enviar el mensaje
            WhatsAppApiClient.send_message(message_payload)
    except Exception as e:
        print(f"ERROR al notificar sobre resolución de soporte: {e}")

    return jsonify({"message": "La conversación ha sido marcada como resuelta."})

@bp.route('/soporte/resoluciones', methods=['GET'])
@admin_required
def get_resoluciones(current_user):
    resoluciones = SoporteResolucionRoute.get_all()
    data = []
    for r in resoluciones:
        cliente_nombre = "N/A"
        if r.conversacion and r.conversacion.perfil_cliente:
            cliente_nombre = (r.conversacion.perfil_cliente.usuario.nombre if r.conversacion.perfil_cliente.usuario 
                              else r.conversacion.perfil_cliente.nombre)
        elif r.ticket and r.ticket.perfil_cliente:
            cliente_nombre = (r.ticket.perfil_cliente.usuario.nombre if r.ticket.perfil_cliente.usuario 
                              else r.ticket.perfil_cliente.nombre)
        data.append({
            "resolucion_id": r.resolucion_id, "tipo_resolucion": r.tipo_resolucion,
            "cliente_nombre": cliente_nombre, "asesor_nombre": r.asesor.nombre if r.asesor else "N/A",
            "fecha_creacion": r.fecha_creacion.isoformat(), "estado_resolucion": r.estado_resolucion,
            "causa_problema": r.causa_problema, "notas": r.notas
        })
    return jsonify(data)

# --- ENDPOINTS PARA GESTIONAR DISPONIBILIDAD (CORREGIDOS) ---

@bp.route('/disponibilidad', methods=['GET', 'OPTIONS']) # Se añade OPTIONS
@admin_required
def get_disponibilidad(current_user):
    """Obtiene todos los horarios para el administrador logueado."""
    slots = DisponibilidadAsesorRoute.get_by_asesor_id(current_user.usuario_id)
    return jsonify([{
        "id": slot.id,
        "fecha_hora_inicio": slot.fecha_hora_inicio.isoformat(),
        "esta_reservado": slot.esta_reservado
    } for slot in slots])

@bp.route('/disponibilidad', methods=['POST', 'OPTIONS']) # Se añade OPTIONS
@admin_required
def add_disponibilidad(current_user):
    """Añade un nuevo horario de disponibilidad para el administrador logueado."""
    data = request.get_json()
    fecha_str = data.get('fecha_hora_inicio')
    if not fecha_str:
        return jsonify({"message": "Falta la fecha y hora"}), 400
    
    fecha_obj = datetime.fromisoformat(fecha_str)
    nuevo_slot = DisponibilidadAsesorRoute.create(fecha_obj, current_user.usuario_id)
    return jsonify({"message": "Horario añadido exitosamente", "id": nuevo_slot.id}), 201

@bp.route('/disponibilidad/<int:slot_id>', methods=['DELETE', 'OPTIONS']) # Se añade OPTIONS
@admin_required
def delete_disponibilidad(current_user, slot_id):
    """Elimina un horario de disponibilidad."""
    slot = DisponibilidadAsesorRoute.get_by_id(slot_id)
    if not slot or slot.asesor_id != current_user.usuario_id:
        return jsonify({"message": "No tienes permiso para eliminar este horario"}), 403

    if DisponibilidadAsesorRoute.delete(slot_id):
        return jsonify({"message": "Horario eliminado"})
    return jsonify({"message": "No se pudo eliminar el horario (puede que esté reservado o no exista)"}), 400

@bp.route('/pedidos/<int:pedido_id>/enviar', methods=['POST', 'OPTIONS'])
@admin_required
def marcar_pedido_enviado(current_user, pedido_id):
    """Marca un pedido como 'en_camino'."""
    pedido = PedidoRoute.get_pedido_by_id(pedido_id)
    if not pedido or pedido.estado != 'pagado':
        return jsonify({"message": "Este pedido no se puede marcar como enviado."}), 400
    
    PedidoRoute.update_order_state(pedido_id, 'en_camino')
    # Opcional: Notificar al cliente
    return jsonify({"message": f"Pedido #{pedido_id} marcado como 'en camino'."})

@bp.route('/pedidos/<int:pedido_id>/completar', methods=['POST', 'OPTIONS'])
@admin_required
def marcar_pedido_completado(current_user, pedido_id):
    """Marca un pedido como 'completo'."""
    pedido = PedidoRoute.get_pedido_by_id(pedido_id)
    if not pedido or pedido.estado != 'en_camino':
        return jsonify({"message": "Este pedido no se puede marcar como completado."}), 400
        
    PedidoRoute.update_order_state(pedido_id, 'completo')
    # Opcional: Notificar al cliente y solicitar reseña
    return jsonify({"message": f"Pedido #{pedido_id} marcado como 'completo'."})

@bp.route('/pedidos/batch-update', methods=['POST', 'OPTIONS'])
@admin_required
def batch_update_pedidos(current_user):
    """
    Recibe un lote de actualizaciones para pedidos y detalles,
    y las aplica en una sola transacción.
    """
    print("\n--- INICIANDO BATCH UPDATE ---")
    data = request.get_json()
    print(f"DEBUG: Payload recibido del frontend: {data}")

    actualizaciones = data.get('actualizaciones')

    if not actualizaciones:
        print("ERROR: No se proporcionaron actualizaciones en el payload.")
        return jsonify({"message": "No se proporcionaron actualizaciones."}), 400

    try:
        for i, update in enumerate(actualizaciones):
            print(f"\nProcesando actualización #{i+1}: {update}")
            pedido_id = update.get('pedido_id')
            if not pedido_id: 
                print(f"  > Omitiendo actualización #{i+1} por falta de pedido_id.")
                continue

            if 'nuevo_estado' in update:
                print(f"  > Acción: Actualizar estado del Pedido {pedido_id} a '{update['nuevo_estado']}'")
                PedidoRoute.update_order_state(pedido_id, update['nuevo_estado'])

            if 'detalles' in update:
                for detalle_update in update['detalles']:
                    detalle_id = detalle_update.get('detalle_id')
                    nuevo_precio_str = detalle_update.get('nuevo_precio_pagado')
                    
                    print(f"  > Procesando detalle ID: {detalle_id} con nuevo precio (str): '{nuevo_precio_str}'")
                    
                    if detalle_id is not None and nuevo_precio_str is not None and nuevo_precio_str != '':
                        nuevo_precio_decimal = decimal.Decimal(nuevo_precio_str)
                        print(f"    > Acción: Actualizar precio del Detalle {detalle_id} a {nuevo_precio_decimal}")
                        DetallePedidoRoute.update_precio_pagado(detalle_id, nuevo_precio_decimal)
            
            print(f"  > Acción: Recalcular monto total del Pedido {pedido_id}")
            PedidoRoute.recalculate_order_total(pedido_id)

        print("\nCommit de todos los cambios a la base de datos...")
        db.session.commit()
        print("--- BATCH UPDATE COMPLETADO EXITOSAMENTE ---")
        
        return jsonify({"message": f"{len(actualizaciones)} pedidos han sido actualizados exitosamente."})

    except Exception as e:
        db.session.rollback()
        # --- CAPTURA DE ERROR DETALLADA ---
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! OCURRIÓ UN ERROR EN BATCH UPDATE !!!")
        print(f"!!! Tipo de Error: {type(e).__name__}")
        print(f"!!! Mensaje de Error: {e}")
        import traceback
        traceback.print_exc() # Imprime el traceback completo en la consola
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # --- FIN DE CAPTURA DE ERROR ---
        
        return jsonify({"message": "Ocurrió un error y no se aplicó ningún cambio. Revisa la consola del servidor."}), 500


@bp.route('/pedidos/<int:pedido_id>/detalles-completos', methods=['GET', 'OPTIONS'])
@admin_required
def get_detalles_completos_pedido(current_user, pedido_id):
    """Devuelve un pedido con todos sus items para la vista modal."""
    pedido = PedidoRoute.get_full_order_details(pedido_id)
    if not pedido:
        return jsonify({"message": "Pedido no encontrado"}), 404

    pedido_data = {
        "pedido_id": pedido.pedido_id,
        "cliente_nombre": pedido.perfil_cliente.nombre,
        "estado": pedido.estado,
        "monto_total": float(pedido.monto_total or 0),
        "items": [{
            "nombre_producto": d.nombre_producto_historico,
            "cantidad": d.respuestas_requisitos.get('Cantidad', 1),
            "precio_final": float(d.precio_pagado or d.precio_unitario_historico)
        } for d in pedido.detalles]
    }
    return jsonify(pedido_data)

@bp.route('/reuniones-agendadas', methods=['GET', 'OPTIONS'])
@admin_required
def get_reuniones_agendadas(current_user):
    """Devuelve los horarios reservados del asesor logueado."""
    reuniones = DisponibilidadAsesorRoute.get_reserved_by_asesor_id(current_user.usuario_id)
    
    reuniones_data = []
    for reunion in reuniones:
        cliente_nombre = "No disponible"
        if reunion.solicitud_asignada and reunion.solicitud_asignada.perfil_cliente:
            cliente_nombre = reunion.solicitud_asignada.perfil_cliente.nombre or "Cliente sin nombre"
        
        reuniones_data.append({
            "id": reunion.id,
            "fecha_hora_inicio": reunion.fecha_hora_inicio.isoformat(),
            "cliente_nombre": cliente_nombre,
            "detalles_solicitud": reunion.solicitud_asignada.detalles_adicionales if reunion.solicitud_asignada else ""
        })
        
    return jsonify(reuniones_data)



@bp.route('/disponibilidad/crear-lote', methods=['POST', 'OPTIONS'])
@admin_required
def add_disponibilidad_en_lote(current_user):
    data = request.get_json()
    
    try:
        # Extraemos los datos del payload
        fecha_inicio_str = data['fecha_inicio']
        fecha_fin_str = data['fecha_fin']
        dias_semana = set(data['dias_semana'])
        hora_inicio = time.fromisoformat(data['hora_inicio'])
        hora_fin = time.fromisoformat(data['hora_fin'])
        duracion_slot_minutos = int(data['duracion_slot_minutos'])

        # --- CORRECCIÓN DEL FORMATO DE FECHA ---
        # Reemplazamos la 'Z' por '+00:00' para que sea compatible con fromisoformat()
        if fecha_inicio_str.endswith('Z'):
            fecha_inicio_str = fecha_inicio_str[:-1] + '+00:00'
        if fecha_fin_str.endswith('Z'):
            fecha_fin_str = fecha_fin_str[:-1] + '+00:00'
        
        fecha_inicio = datetime.fromisoformat(fecha_inicio_str).date()
        fecha_fin = datetime.fromisoformat(fecha_fin_str).date()
        
    except (KeyError, TypeError, ValueError) as e:
        current_app.logger.error(f"ERROR de formato/parámetro en crear-lote: {e}")
        return jsonify({"message": f"Faltan parámetros o tienen formato incorrecto: {e}"}), 400

    slots_creados = 0
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() in dias_semana:
            hora_actual = datetime.combine(fecha_actual, hora_inicio)
            hora_limite = datetime.combine(fecha_actual, hora_fin)
            
            while hora_actual < hora_limite:
                # Se podría añadir una lógica para evitar duplicados si se desea
                DisponibilidadAsesorRoute.create(hora_actual, current_user.usuario_id)
                slots_creados += 1
                hora_actual += timedelta(minutes=duracion_slot_minutos)
        fecha_actual += timedelta(days=1)
    
    db.session.commit()

    return jsonify({"message": f"Se han creado {slots_creados} nuevos horarios exitosamente."}), 201

@bp.route('/tool/perfiles-cliente', methods=['GET', 'OPTIONS'])
@admin_required
def search_perfiles_cliente(current_user):
    """Busca o lista perfiles de cliente con paginación."""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if query:
        pagination = PerfilClienteRoute.search_by_query(query, page, per_page)
    else:
        pagination = PerfilClienteRoute.get_all_paginated(page, per_page)
    
    perfiles = pagination.items
    
    perfiles_data = [{
        "id": p.perfil_cliente_id,
        "nombre": p.nombre,
        "telefono": p.telefono_vinculado,
        "bot_pausado": p.bot_pausado
    } for p in perfiles]
    
    return jsonify({
        "items": perfiles_data,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages
    })

@bp.route('/tool/perfiles-cliente/<int:perfil_id>/pausar-bot', methods=['POST', 'OPTIONS'])
@admin_required
def pausar_bot_cliente(current_user, perfil_id):
    """Pausa el bot para un cliente específico."""
    PerfilClienteRoute.update_bot_status(perfil_id, True) # Necesitaremos esta nueva función
    db.session.commit()
    return jsonify({"message": "El bot ha sido pausado para este cliente."})

@bp.route('/tool/perfiles-cliente/<int:perfil_id>/reanudar-bot', methods=['POST', 'OPTIONS'])
@admin_required
def reanudar_bot_cliente(current_user, perfil_id):
    """Reanuda el bot para un cliente específico."""
    PerfilClienteRoute.update_bot_status(perfil_id, False)
    db.session.commit()
    return jsonify({"message": "El bot ha sido reanudado para este cliente."})


@bp.route('/tool/pedidos', methods=['GET', 'POST', 'OPTIONS'])
@admin_required
def tool_pedidos_general(current_user):
    """
    Maneja la obtención de la lista de todos los pedidos (GET)
    y la creación de un nuevo pedido (POST).
    """
    # --- Lógica para GET (Listar todos los pedidos) ---
    if request.method == 'GET':
        pedidos = Pedido.query.order_by(Pedido.fecha_creacion.desc()).all()
        pedidos_data = []
        for p in pedidos:
            nombre_cliente = p.perfil_cliente.nombre if p.perfil_cliente else "N/A"
            pedidos_data.append({
                "pedido_id": p.pedido_id,
                "cliente_nombre": nombre_cliente,
                "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
                "estado": p.estado,
                "monto_total": float(p.monto_total or 0)
            })
        return jsonify(pedidos_data)
    
    # --- Lógica para POST (Crear un nuevo pedido) ---
    if request.method == 'POST':
        data = request.get_json()
        perfil_cliente_id = data.get('perfil_cliente_id')
        detalles_data = data.get('detalles', [])

        if not perfil_cliente_id:
            return jsonify({"message": "Se requiere un cliente para crear el pedido"}), 400

        try:
            nuevo_pedido = Pedido(perfil_cliente_id=perfil_cliente_id, estado=data.get('estado', 'pendiente'))
            db.session.add(nuevo_pedido)
            db.session.flush() # Para obtener el ID del nuevo pedido antes del commit

            for detalle_data in detalles_data:
                producto = Producto.query.get(detalle_data.get('producto_id'))
                if not producto: continue

                nuevo_detalle = DetallePedido(
                    pedido_id=nuevo_pedido.pedido_id,
                    producto_id=producto.producto_id,
                    nombre_producto_historico=producto.nombre_producto,
                    respuestas_requisitos=detalle_data.get('respuestas_requisitos', {}),
                    precio_unitario_historico=decimal.Decimal(detalle_data.get('precio_unitario_historico', 0)),
                    precio_pagado=decimal.Decimal(detalle_data.get('precio_pagado', 0))
                )
                db.session.add(nuevo_detalle)
            
            PedidoRoute.recalculate_order_total(nuevo_pedido.pedido_id)
            db.session.commit()
            return jsonify({"message": "Pedido creado exitosamente", "pedido_id": nuevo_pedido.pedido_id}), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear pedido manual: {e}")
            return jsonify({"message": "Error interno al crear el pedido."}), 500


@bp.route('/tool/pedidos/<int:pedido_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
@admin_required
def tool_pedidos_especifico(current_user, pedido_id):
    """
    Maneja la obtención (GET), actualización (PUT) y eliminación (DELETE) 
    de un pedido específico.
    """
    
    # --- Lógica para GET (Obtener un pedido para editar) ---
    if request.method == 'GET':
        pedido = PedidoRoute.get_full_order_details(pedido_id)
        if not pedido:
            return jsonify({"message": "Pedido no encontrado"}), 404
        
        pedido_data = {
            "pedido_id": pedido.pedido_id,
            "perfil_cliente_id": pedido.perfil_cliente_id,
            "estado": pedido.estado,
            "detalles": [{
                "detalle_pedido_id": d.detalle_pedido_id,
                "producto_id": d.producto_id,
                "respuestas_requisitos": d.respuestas_requisitos if d.respuestas_requisitos else {},
                "precio_unitario_historico": float(d.precio_unitario_historico or 0),
                "precio_pagado": float(d.precio_pagado or d.precio_unitario_historico or 0)
            } for d in pedido.detalles]
        }
        return jsonify(pedido_data)

    # --- Lógica para PUT (Actualizar un pedido) ---
    if request.method == 'PUT':
        data = request.get_json()
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({"message": "Pedido no encontrado"}), 404

        try:
            # 1. Actualizar datos del pedido principal
            pedido.estado = data.get('estado', pedido.estado)
            pedido.perfil_cliente_id = data.get('perfil_cliente_id', pedido.perfil_cliente_id)

            # 2. Sincronizar detalles del pedido
            detalles_payload = data.get('detalles', [])
            ids_detalles_existentes = {d.detalle_pedido_id for d in pedido.detalles}
            ids_detalles_payload = {d.get('detalle_pedido_id') for d in detalles_payload if d.get('detalle_pedido_id')}

            # 2a. Eliminar detalles que ya no están en el payload
            for detalle_id_a_eliminar in ids_detalles_existentes - ids_detalles_payload:
                detalle_a_eliminar = DetallePedido.query.get(detalle_id_a_eliminar)
                if detalle_a_eliminar:
                    db.session.delete(detalle_a_eliminar)

            # 2b. Actualizar detalles existentes y añadir nuevos
            for detalle_data in detalles_payload:
                detalle_id = detalle_data.get('detalle_pedido_id')
                producto_id = detalle_data.get('producto_id')
                if not producto_id: continue # Ignorar items sin producto
                
                producto = Producto.query.get(producto_id)
                if not producto: continue

                # Parsear respuestas, asegurándose de que sea un dict
                respuestas = detalle_data.get('respuestas_requisitos', {})
                if isinstance(respuestas, str):
                    try:
                        respuestas = json.loads(respuestas)
                    except json.JSONDecodeError:
                        respuestas = {}

                if detalle_id: # Es un detalle existente, lo actualizamos
                    detalle_a_actualizar = DetallePedido.query.get(detalle_id)
                    if detalle_a_actualizar:
                        detalle_a_actualizar.producto_id = producto.producto_id
                        detalle_a_actualizar.nombre_producto_historico = producto.nombre_producto
                        detalle_a_actualizar.respuestas_requisitos = respuestas
                        detalle_a_actualizar.precio_unitario_historico = decimal.Decimal(detalle_data.get('precio_unitario_historico', 0))
                        detalle_a_actualizar.precio_pagado = decimal.Decimal(detalle_data.get('precio_pagado', 0))
                else: # Es un detalle nuevo, lo creamos
                    nuevo_detalle = DetallePedido(
                        pedido_id=pedido.pedido_id,
                        producto_id=producto.producto_id,
                        nombre_producto_historico=producto.nombre_producto,
                        respuestas_requisitos=respuestas,
                        precio_unitario_historico=decimal.Decimal(detalle_data.get('precio_unitario_historico', 0)),
                        precio_pagado=decimal.Decimal(detalle_data.get('precio_pagado', 0))
                    )
                    db.session.add(nuevo_detalle)
            
            # 3. Recalcular el total y confirmar
            PedidoRoute.recalculate_order_total(pedido_id)
            db.session.commit()
            return jsonify({"message": "Pedido actualizado exitosamente."})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al actualizar pedido manual: {e}")
            return jsonify({"message": "Error interno al actualizar el pedido."}), 500

    # --- Lógica para DELETE (Eliminar un pedido) ---
    if request.method == 'DELETE':
        if PedidoRoute.delete_by_id(pedido_id):
            db.session.commit()
            return jsonify({"message": "Pedido eliminado exitosamente."})
        return jsonify({"message": "Pedido no encontrado."}), 404
    
@bp.route('/tool/clientes-list', methods=['GET', 'OPTIONS'])
@admin_required
def get_clientes_list(current_user):
    """Devuelve una lista simple de todos los clientes para los formularios."""
    try:
        clientes = PerfilCliente.query.order_by(PerfilCliente.nombre.asc()).all()
        return jsonify([{"id": c.perfil_cliente_id, "nombre": c.nombre or c.telefono_vinculado} for c in clientes])
    except Exception as e:
        current_app.logger.error(f"Error al obtener lista de clientes: {e}")
        return jsonify({"message": "No se pudo obtener la lista de clientes."}), 500

@bp.route('/tool/productos-list', methods=['GET', 'OPTIONS'])
@admin_required
def get_productos_list(current_user):
    """Devuelve una lista simple de todos los productos activos para los formularios."""
    try:
        productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre_producto.asc()).all()
        return jsonify([{"id": p.producto_id, "nombre": p.nombre_producto} for p in productos])
    except Exception as e:
        current_app.logger.error(f"Error al obtener lista de productos: {e}")
        return jsonify({"message": "No se pudo obtener la lista de productos."}), 500
    

# ... (todo el código existente de admin_api_routes.py) ...

# --- ENDPOINTS CRUD PARA PERFILES DE CLIENTE (TOOL) ---

@bp.route('/tool/perfiles-cliente', methods=['POST'])
@admin_required
def tool_create_perfil_cliente(current_user):
    data = request.get_json()
    if not data or not data.get('telefono_vinculado'):
        return jsonify({"message": "El teléfono es un campo requerido."}), 400
    
    # Podríamos añadir más validaciones aquí (ej, si el teléfono ya existe)
    
    try:
        # Se crea un PerfilCliente sin usuario asociado, como si viniera de WhatsApp
        nuevo_perfil = PerfilClienteRoute.create(
            phone_number=data['telefono_vinculado'],
            nombre=data.get('nombre')
        )
        return jsonify({ "message": "Perfil de cliente creado exitosamente.", "id": nuevo_perfil.perfil_cliente_id }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al crear perfil de cliente: {e}")
        return jsonify({"message": "Error interno al crear el perfil."}), 500

@bp.route('/tool/perfiles-cliente/<int:perfil_id>', methods=['GET'])
@admin_required
def tool_get_perfil_cliente(current_user, perfil_id):
    perfil = db.session.get(PerfilCliente, perfil_id)
    if not perfil:
        return jsonify({"message": "Perfil no encontrado"}), 404
    
    # Devolvemos un objeto plano para el formulario del frontend
    return jsonify({
        "perfil_cliente_id": perfil.perfil_cliente_id,
        "nombre": perfil.nombre,
        "telefono_vinculado": perfil.telefono_vinculado,
        "rut": perfil.rut,
        "direccion": perfil.direccion
    })

@bp.route('/tool/perfiles-cliente/<int:perfil_id>', methods=['PUT'])
@admin_required
def tool_update_perfil_cliente(current_user, perfil_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No se recibieron datos para actualizar."}), 400
        
    try:
        perfil = PerfilClienteRoute.update_by_id(perfil_id, data)
        if not perfil:
            return jsonify({"message": "Perfil no encontrado"}), 404
        
        # Opcional: Si el perfil tiene un usuario asociado, también actualizamos su nombre
        if perfil.usuario and 'nombre' in data:
            perfil.usuario.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Perfil actualizado exitosamente."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar perfil de cliente: {e}")
        return jsonify({"message": "Error interno al actualizar el perfil."}), 500

@bp.route('/tool/perfiles-cliente/<int:perfil_id>', methods=['DELETE'])
@admin_required
def tool_delete_perfil_cliente(current_user, perfil_id):
    perfil = db.session.get(PerfilCliente, perfil_id)
    if not perfil:
        return jsonify({"message": "Perfil no encontrado"}), 404
    
    # Aquí podrías añadir lógica compleja, como qué hacer con los pedidos asociados.
    # Por ahora, simplemente lo borramos. Cuidado en producción.
    try:
        db.session.delete(perfil)
        db.session.commit()
        return jsonify({"message": "Perfil de cliente eliminado."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar perfil de cliente: {e}")
        return jsonify({"message": "Error: El perfil podría tener datos asociados (pedidos, etc.) que impiden su borrado."}), 409


@bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats(current_user):
    try:
        health_metrics = DashboardRoute.get_system_health()
        kpi_metrics = DashboardRoute.get_business_kpis()

        # Unimos ambos diccionarios para una sola respuesta
        stats = {**health_metrics, **kpi_metrics}

        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Error al obtener estadísticas del dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": "Error al calcular las estadísticas."}), 500


# return bp # Esta línea ya debería existir al final de tu archivo
