# app/api/portal_api_routes.py
from flask import Blueprint, jsonify, request, current_app
from app.api.auth_utils import token_required
from app.routes import (
    PedidoRoute, ReseñaRoute, TicketProductoRoute, ProductoRoute,
    DetallePedidoRoute, PreciosProductoRoute, SolicitudAsesorRoute, 
    DisponibilidadAsesorRoute, ConversacionRoute, MensajeRoute, PerfilClienteRoute
)
from app.services import s3_service
from datetime import datetime, timedelta
import decimal

bp = Blueprint('portal_api', __name__, url_prefix='/api/portal')

# --- ENDPOINTS DE CATÁLOGO ---
@bp.route('/catalogo/categorias', methods=['GET'])
@token_required
def get_categorias(current_user):
    categorias = ProductoRoute.obtener_categorias_productos()
    return jsonify(categorias)

@bp.route('/catalogo/productos', methods=['GET'])
@token_required
def get_productos_por_categoria(current_user):
    categoria = request.args.get('categoria')
    if not categoria: return jsonify({"message": "Parámetro 'categoria' es requerido."}), 400
    productos = ProductoRoute.obtener_productos_por_categoria(categoria)
    return jsonify(productos)

@bp.route('/productos/<int:producto_id>/detalles', methods=['GET'])
@token_required
def get_producto_detalles(current_user, producto_id):
    detalles = ProductoRoute.get_product_details_for_portal(producto_id)
    if not detalles: return jsonify({"message": "Producto no encontrado"}), 404
    return jsonify(detalles)

# --- ENDPOINTS DE GESTIÓN DE PEDIDO (CARRITO) ---
@bp.route('/carrito', methods=['GET'])
@token_required
def get_carrito_actual(current_user):
    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    pedido_carrito = PedidoRoute.get_or_create_cart_order(perfil_id)
    resumen = PedidoRoute.get_order_summary_data(pedido_carrito.pedido_id)
    return jsonify({
        "pedido_id": pedido_carrito.pedido_id,
        "items": resumen.get('items', []),
        "total": resumen.get('grand_total', 0)
    })

@bp.route('/carrito/items', methods=['POST'])
@token_required
def agregar_item_al_carrito(current_user):
    data = request.get_json()
    producto_id_raw = data.get('producto_id')
    respuestas = data.get('requisitos')
    print(">>> DATOS RECIBIDOS EN /carrito/items:", data)

    # --- VALIDACIÓN Y CONVERSIÓN SEGURA ---
    try:
        producto_id = int(producto_id_raw)
    except (ValueError, TypeError):
        return jsonify({"message": "ID de producto inválido. Debe ser un número."}), 400

    if not current_user.perfil_cliente:
         return jsonify({"message": "Usuario no tiene perfil de cliente."}), 403

    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    pedido_carrito = PedidoRoute.get_or_create_cart_order(perfil_id)
    
    producto = ProductoRoute.get_product_by_id_for_portal(producto_id)
    if not producto:
        return jsonify({"message": "Producto no encontrado"}), 404

    # Lógica de cálculo de precio (simplificada)
    precio_calculado = decimal.Decimal('0.0')
    if producto.precios:
        precio_calculado = producto.precios[0].precio_unitario

    DetallePedidoRoute.add_item_to_order(
        pedido_id=pedido_carrito.pedido_id, producto_id=producto_id,
        nombre_producto=producto.nombre_producto, precio_unitario=precio_calculado,
        sku=producto.sku, respuestas=respuestas
    )
    return jsonify({"message": "Producto añadido al carrito"}), 201

@bp.route('/carrito/items/<int:detalle_id>', methods=['DELETE'])
@token_required
def quitar_item_del_carrito(current_user, detalle_id):
    if DetallePedidoRoute.remove_item_from_order(detalle_id):
        return jsonify({"message": "Producto eliminado del carrito"})
    return jsonify({"message": "Producto no encontrado en el carrito"}), 404

@bp.route('/carrito/checkout', methods=['POST'])
@token_required
def finalizar_compra(current_user):
    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    pedido_carrito = PedidoRoute.get_or_create_cart_order(perfil_id)
    if not pedido_carrito or not pedido_carrito.detalles:
        return jsonify({"message": "Tu carrito está vacío."}), 400
    PedidoRoute.update_order_state(pedido_carrito.pedido_id, 'esperando_pago')
    return jsonify({"message": "Pedido finalizado, esperando pago."})

@bp.route('/pedidos/<int:pedido_id>/comprobante', methods=['POST'])
@token_required
def subir_comprobante(current_user, pedido_id):
    if 'file' not in request.files: return jsonify({"message": "No se encontró el archivo"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"message": "No se seleccionó ningún archivo"}), 400
    
    # Esta línea ahora funcionará gracias a la importación de current_app
    s3_path = f"comprobantes/{current_user.usuario_id}/{pedido_id}_{file.filename}"
    s3_service.upload_file_to_s3(file.read(), current_app.config['S3_BUCKET_NAME'], s3_path)
    
    PedidoRoute.set_receipt_path(pedido_id, s3_path)
    PedidoRoute.update_order_state(pedido_id, 'en_revision')
    return jsonify({"message": "Comprobante subido, tu pedido está en revisión."})


@bp.route('/pedidos/<int:pedido_id>/poner-en-espera', methods=['POST'])
@token_required
def poner_pedido_en_espera(current_user, pedido_id):
    data = request.get_json()
    dias_espera = data.get('dias_espera', 7)
    fecha_maxima = datetime.utcnow() + timedelta(days=int(dias_espera))
    PedidoRoute.set_on_hold(pedido_id, fecha_maxima)
    return jsonify({"message": f"Tu pedido ha sido puesto en espera."})

# --- ENDPOINTS DE HISTORIAL, RESEÑAS Y SOLICITUDES ---
@bp.route('/pedidos/historial', methods=['GET'])
@token_required
def get_mis_pedidos(current_user):
    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    pedidos = PedidoRoute.get_all_for_profile(perfil_id)
    pedidos_data = [{ "pedido_id": p.pedido_id, "fecha_creacion": p.fecha_creacion.isoformat(), "estado": p.estado, "monto_total": float(p.monto_total or 0)} for p in pedidos]
    return jsonify(pedidos_data)



@bp.route('/solicitar-producto', methods=['POST'])
@token_required
def solicitar_producto(current_user):
    data = request.get_json()
    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    if not all(k in data for k in ['nombre_producto', 'descripcion']): return jsonify({"message": "El nombre y la descripción son requeridos."}), 400
    TicketProductoRoute.create_ticket_completo(perfil_id, data['nombre_producto'], data['descripcion'])
    return jsonify({"message": "Tu solicitud ha sido enviada."}), 201

@bp.route('/resenas', methods=['GET', 'POST'])
@token_required
def handle_resenas(current_user):
    if request.method == 'GET':
        try:
            # CORRECCIÓN 1: Usar el nombre del método correcto.
            resenas = ReseñaRoute.get_all_for_profile(current_user.perfil_cliente.perfil_cliente_id)
            
            # CORRECCIÓN 3: Construir el diccionario manualmente.
            resenas_data = [{
                "reseña_id": r.reseña_id,
                "producto_id": r.producto_id,
                "producto_nombre": r.producto.nombre_producto if r.producto else "Producto eliminado",
                "calificacion": r.calificacion,
                "comentario": r.comentario,
                "fecha_creacion": r.fecha_creacion.isoformat()
            } for r in resenas]
            
            return jsonify(resenas_data)
        except Exception as e:
            current_app.logger.error(f"Error al obtener reseñas: {e}")
            return jsonify({"message": "Error interno al obtener reseñas"}), 500

    if request.method == 'POST':
        data = request.get_json()
        if not data or not all(k in data for k in ['producto_id', 'calificacion']):
            return jsonify({"message": "Faltan datos para la reseña"}), 400
        
        try:
            # Aquí la creación estaba bien, la mantenemos.
            nueva_resena = ReseñaRoute.create(
                perfil_cliente_id=current_user.perfil_cliente.perfil_cliente_id,
                producto_id=data['producto_id'],
                calificacion=data['calificacion'],
                comentario=data.get('comentario', '') # Usamos .get para el comentario opcional
            )
            # Devolvemos el diccionario del nuevo objeto.
            return jsonify({
                "reseña_id": nueva_resena.reseña_id,
                "producto_id": nueva_resena.producto_id,
                "producto_nombre": nueva_resena.producto.nombre_producto,
                "calificacion": nueva_resena.calificacion,
                "comentario": nueva_resena.comentario,
                "fecha_creacion": nueva_resena.fecha_creacion.isoformat()
            }), 201
        except Exception as e:
            current_app.logger.error(f"Error al crear reseña: {e}")
            return jsonify({"message": "Error interno al crear la reseña"}), 500








@bp.route('/pedidos/<int:pedido_id>/repetir', methods=['POST'])
@token_required
def repetir_pedido(current_user, pedido_id):
    perfil_id = current_user.perfil_cliente.perfil_cliente_id
    nuevo_pedido = PedidoRoute.replicate_order(pedido_id, perfil_id)
    if nuevo_pedido:
        return jsonify({"message": "El pedido ha sido copiado a tu carrito actual.", "nuevo_pedido_id": nuevo_pedido.pedido_id})
    return jsonify({"message": "No se pudo repetir el pedido."}), 404

@bp.route('/productos-para-resena', methods=['GET'])
@token_required
def get_productos_para_resena(current_user):
    """Devuelve los productos de pedidos completados que el usuario aún no ha calificado."""
    try:
        # CORRECCIÓN 2: Usar el nombre del método correcto.
        productos = ReseñaRoute.get_productos_para_reseña(current_user.perfil_cliente.perfil_cliente_id)
        return jsonify([{'producto_id': p.producto_id, 'nombre_producto': p.nombre_producto} for p in productos])
    except Exception as e:
        current_app.logger.error(f"Error al obtener productos para reseña: {e}")
        return jsonify({"message": "Error interno al obtener productos"}), 500

@bp.route('/resenas', methods=['POST'])
@token_required
def crear_resena(current_user):
    data = request.get_json()
    producto_id = data.get('producto_id')
    calificacion = data.get('calificacion')
    comentario = data.get('comentario')
    perfil_id = current_user.perfil_cliente.perfil_cliente_id

    if not all([producto_id, calificacion, perfil_id]):
        return jsonify({"message": "Faltan datos para crear la reseña."}), 400
    
    if not ReseñaRoute.ha_comprado_producto(perfil_id, producto_id):
        return jsonify({"message": "Solo puedes dejar reseñas de productos que has comprado."}), 403

    ReseñaRoute.create(perfil_id, producto_id, calificacion, comentario)
    return jsonify({"message": "¡Gracias por tu reseña!"}), 201

@bp.route('/resenas/<int:resena_id>', methods=['PUT'])
@token_required
def update_resena(current_user, resena_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No se recibieron datos"}), 400
    
    # Verificamos que la reseña pertenezca al usuario antes de actualizar
    reseña = ReseñaRoute.get_by_id(resena_id) # Asumiendo que existe un get_by_id
    if not reseña or reseña.perfil_cliente_id != current_user.perfil_cliente.perfil_cliente_id:
        return jsonify({"message": "Reseña no encontrada o no te pertenece"}), 404

    reseña_actualizada = ReseñaRoute.update(resena_id, data)
    if reseña_actualizada:
         return jsonify({
            "reseña_id": reseña_actualizada.reseña_id,
            "producto_nombre": reseña_actualizada.producto.nombre_producto,
            "calificacion": reseña_actualizada.calificacion,
            "comentario": reseña_actualizada.comentario,
            "fecha_creacion": reseña_actualizada.fecha_creacion.isoformat()
        })
    return jsonify({"message": "No se pudo actualizar la reseña"}), 500

@bp.route('/datos-pago', methods=['GET'])
@token_required
def get_datos_pago(current_user):
    """Devuelve los datos de la cuenta bancaria para realizar el pago."""
    payment_data = {
        'banco': current_app.config.get('BANK_NAME'),
        'titular': current_app.config.get('ACCOUNT_HOLDER'),
        'numero_cuenta': current_app.config.get('ACCOUNT_NUMBER'),
        'rut': current_app.config.get('HOLDER_RUT'),
        'email': current_app.config.get('HOLDER_EMAIL')
    }
    return jsonify(payment_data)

@bp.route('/carrito/ahorro-potencial', methods=['GET'])
@token_required
def get_ahorro_potencial(current_user):
    """Calcula y devuelve el ahorro potencial para el carrito actual del usuario."""
    try:
        carrito = PedidoRoute.get_or_create_cart_order(current_user.perfil_cliente.perfil_cliente_id)
        if not carrito:
            return jsonify({"ahorro_potencial": 0})
        
        ahorro = PedidoRoute.calculate_potential_savings(carrito.pedido_id)
        return jsonify({"ahorro_potencial": float(ahorro)})

    except Exception as e:
        current_app.logger.error(f"Error al calcular ahorro potencial: {e}")
        return jsonify({"message": "Error interno al calcular ahorro"}), 500


@bp.route('/soporte/tickets', methods=['GET'])
@token_required
def get_mis_tickets(current_user):
    """Devuelve todos los tickets de solicitud de producto para el cliente logueado."""
    try:
        tickets = TicketProductoRoute.get_by_profile_id(current_user.perfil_cliente.perfil_cliente_id)
        
        # Construimos la respuesta manualmente para asegurar el formato
        tickets_data = [{
            "id": ticket.ticket_id,
            "nombre_producto": ticket.nombre_producto_deseado,
            "descripcion": ticket.descripcion,
            "estado": ticket.estado,
            "fecha_creacion": ticket.fecha_creacion.isoformat()
        } for ticket in tickets]
        
        return jsonify(tickets_data)
    except Exception as e:
        current_app.logger.error(f"Error al obtener tickets de soporte para el cliente: {e}")
        return jsonify({"message": "Error interno al obtener las solicitudes"}), 500
    

@bp.route('/soporte/solicitar-asesor', methods=['POST', 'OPTIONS']) # Se añade OPTIONS
@token_required
def solicitar_asesor(current_user):
    """Gestiona una nueva solicitud de contacto de un cliente."""
    data = request.get_json()
    metodo = data.get('metodo')
    detalles = data.get('detalles')
    disponibilidad_id = data.get('disponibilidad_id')

    if not metodo:
        return jsonify({"message": "El método de contacto es requerido"}), 400
    if metodo == 'reunion' and not disponibilidad_id:
        return jsonify({"message": "Debe seleccionar un horario para la reunión"}), 400

    try:
        asesor_a_asignar_id = None
        
        if metodo == 'reunion':
            slot_a_reservar = DisponibilidadAsesorRoute.get_by_id(disponibilidad_id)
            if not slot_a_reservar or slot_a_reservar.esta_reservado:
                 return jsonify({"message": "El horario seleccionado ya no está disponible."}), 409
            asesor_a_asignar_id = slot_a_reservar.asesor_id

        solicitud = SolicitudAsesorRoute.create(
            perfil_cliente_id=current_user.perfil_cliente.perfil_cliente_id,
            metodo=metodo,
            detalles=detalles,
            asesor_id=asesor_a_asignar_id
        )

        if metodo == 'reunion':
            DisponibilidadAsesorRoute.reserve(disponibilidad_id, solicitud.id)
        
        if metodo == 'whatsapp':
            conversacion = ConversacionRoute.get_active_conversation(current_user.perfil_cliente.perfil_cliente_id)
            if not conversacion:
                conversacion = ConversacionRoute.create_new_conversation(current_user.perfil_cliente.perfil_cliente_id)
            
            ConversacionRoute.update_support_state(conversacion.conversacion_id, 'pendiente')
            
            # --- LÓGICA AÑADIDA PARA REGISTRAR MENSAJE ---
            mensaje_a_registrar = detalles if detalles else "El cliente ha solicitado contactar con un asesor desde la página web."
            MensajeRoute.registrar_mensaje_usuario(
                conversacion_id=conversacion.conversacion_id,
                wam_id=f"solicitud_web_{datetime.utcnow().isoformat()}", # ID único para trazabilidad
                tipo_mensaje='text',
                cuerpo_mensaje=mensaje_a_registrar
            )
            # --- FIN DE LA LÓGICA AÑADIDA ---

        return jsonify({"message": "Tu solicitud ha sido enviada. Un asesor se pondrá en contacto contigo a la brevedad."}), 201
        
    except Exception as e:
        current_app.logger.error(f"Error al solicitar asesor: {e}")
        return jsonify({"message": "Error interno al procesar la solicitud"}), 500


@bp.route('/soporte/disponibilidad-reuniones', methods=['GET', 'OPTIONS']) # Se añade OPTIONS
@token_required
def get_disponibilidad_reuniones(current_user):
    """Devuelve los horarios disponibles para reuniones."""
    slots = DisponibilidadAsesorRoute.get_all_available()
    return jsonify([{
        "id": slot.id,
        "fecha_hora": slot.fecha_hora_inicio.isoformat()
    } for slot in slots])

# --- NUEVOS ENDPOINTS PARA EL PANEL ---

@bp.route('/panel/estadisticas', methods=['GET', 'OPTIONS'])
@token_required
def get_estadisticas_panel(current_user):
    """Devuelve las estadísticas para el dashboard del cliente."""
    stats = PerfilClienteRoute.get_dashboard_stats(current_user.perfil_cliente.perfil_cliente_id)
    return jsonify(stats)

@bp.route('/perfil', methods=['GET', 'OPTIONS'])
@token_required
def get_mi_perfil(current_user):
    """Devuelve los datos del perfil del cliente actual."""
    perfil = current_user.perfil_cliente
    return jsonify({
        "nombre": perfil.nombre or current_user.nombre,
        "rut": perfil.rut,
        "direccion": perfil.direccion,
        "email": current_user.email,
        "telefono": current_user.telefono,
    })

@bp.route('/perfil', methods=['PUT', 'OPTIONS'])
@token_required
def update_mi_perfil(current_user):
    """Actualiza los datos del perfil del cliente."""
    data = request.get_json()
    perfil_actualizado = PerfilClienteRoute.update_by_id(current_user.perfil_cliente.perfil_cliente_id, data)
    if perfil_actualizado:
        return jsonify({"message": "Perfil actualizado exitosamente."})
    return jsonify({"message": "Error al actualizar el perfil"}), 400

@bp.route('/pedidos/<int:pedido_id>/detalles', methods=['GET', 'OPTIONS'])
@token_required
def get_detalles_pedido_cliente(current_user, pedido_id):
    """Devuelve los detalles completos de un pedido específico del cliente."""
    pedido = PedidoRoute.get_full_order_details(pedido_id)

    # Verificación de seguridad: el pedido debe pertenecer al cliente que lo solicita
    if not pedido or pedido.perfil_cliente_id != current_user.perfil_cliente.perfil_cliente_id:
        return jsonify({"message": "Pedido no encontrado o no te pertenece"}), 404

    pedido_data = {
        "pedido_id": pedido.pedido_id,
        "fecha_creacion": pedido.fecha_creacion.isoformat(),
        "estado": pedido.estado,
        "monto_total": float(pedido.monto_total or 0),
        "items": [{
            "nombre_producto": d.nombre_producto_historico,
            "cantidad": (d.respuestas_requisitos or {}).get('Cantidad', 1),
            "precio_final_unitario": float(d.precio_pagado or d.precio_unitario_historico or 0)
        } for d in pedido.detalles]
    }
    return jsonify(pedido_data)