# app/routes/pedido_routes.py
import decimal
from app import db
from app.models import Pedido, DetallePedido, PreciosProducto, PerfilCliente
from typing import Optional, Dict, Any, List
from sqlalchemy import case, func, cast, Text
from sqlalchemy.orm import joinedload
from datetime import datetime

class PedidoRoute:
    @staticmethod
    def get_or_create_cart_order(perfil_cliente_id: int) -> Pedido:
        """Busca un pedido 'pendiente' (carrito) o crea uno nuevo si no existe."""
        pedido = Pedido.query.filter_by(perfil_cliente_id=perfil_cliente_id, estado='pendiente').first()
        if not pedido:
            pedido = Pedido(perfil_cliente_id=perfil_cliente_id, estado='pendiente')
            db.session.add(pedido)
            db.session.commit()
        return pedido

    @staticmethod
    def get_order_summary_data(pedido_id: int) -> dict:
        """
        Calcula el resumen de un pedido de forma robusta.
        Siempre devuelve todos los items, con un total, y el ID de cada detalle.
        """
        # --- CONSULTA CORREGIDA ---
        # Se usa el atributo de la clase DetallePedido.producto en lugar de un string.
        pedido = Pedido.query.options(
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto)
        ).get(pedido_id)
        
        if not pedido:
            return {"items": [], "grand_total": 0}

        items_completos = []
        gran_total = decimal.Decimal('0.0')

        for detalle in pedido.detalles:
            respuestas_cliente = detalle.respuestas_requisitos or {}
            cantidad_cliente = int(respuestas_cliente.get("Cantidad", 1))
            
            precio_unitario = detalle.precio_unitario_historico or decimal.Decimal('0.0')
            
            total_linea = decimal.Decimal(cantidad_cliente) * precio_unitario
            gran_total += total_linea
            
            items_completos.append({
                "detalle_pedido_id": detalle.detalle_pedido_id,
                "product_name": detalle.nombre_producto_historico,
                "quantity": cantidad_cliente,
                "line_total": float(total_linea),
                "requisitos": respuestas_cliente
            })
        
        pedido.monto_total = gran_total
        db.session.commit()

        return { "items": items_completos, "grand_total": float(gran_total) }

    @staticmethod
    def get_all_for_profile(perfil_cliente_id: int) -> List[Pedido]:
        """Obtiene todos los pedidos de un perfil (excepto el carrito 'pendiente')."""
        return Pedido.query.filter(
            Pedido.perfil_cliente_id == perfil_cliente_id,
            Pedido.estado != 'pendiente'
        ).order_by(Pedido.fecha_creacion.desc()).all()

    @staticmethod
    def set_on_hold(pedido_id: int, fecha_maxima: datetime):
        pedido = Pedido.query.get(pedido_id)
        if pedido and pedido.estado == 'pendiente':
            pedido.estado = 'en_espera'
            pedido.fecha_espera_maxima = fecha_maxima
            db.session.commit()
        return pedido
        
    @staticmethod
    def update_order_state(pedido_id: int, nuevo_estado: str):
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            pedido.estado = nuevo_estado
            db.session.commit()

    @staticmethod
    def set_receipt_path(pedido_id: int, path: str):
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            pedido.path_comprobante = path
            db.session.commit()

    # Funciones legacy del bot, se mantienen por compatibilidad
    @staticmethod
    def create_new_order(perfil_cliente_id: int) -> Pedido:
        return PedidoRoute.get_or_create_cart_order(perfil_cliente_id)

    @staticmethod
    def get_active_or_paused_order(perfil_cliente_id: int) -> Optional[Pedido]:
        return Pedido.query.filter(Pedido.perfil_cliente_id == perfil_cliente_id, Pedido.estado.in_(['pendiente', 'en_pausa'])).order_by(case((Pedido.estado == 'pendiente', 0), else_=1)).first()

    @staticmethod
    def get_pending_order(perfil_cliente_id: int) -> Optional[Pedido]:
        return Pedido.query.filter_by(perfil_cliente_id=perfil_cliente_id, estado='pendiente').first()

    @staticmethod
    def get_pedido_by_id(pedido_id: int) -> Optional[Pedido]:
        return Pedido.query.get(pedido_id)

    @staticmethod
    def get_order_in_payment_phase(perfil_cliente_id: int) -> Optional[Pedido]:
        return Pedido.query.filter(Pedido.perfil_cliente_id == perfil_cliente_id, Pedido.estado.in_(['esperando_pago', 'en_revision'])).first()
    
    @staticmethod
    def get_orders_by_status(status: str = None) -> List[Dict[str, Any]]:
        print(f"\n--- DEBUG (PedidoRoute): Buscando pedidos con estado: '{status}' ---")
        
        if status != 'en_espera':
            query = Pedido.query.options(
                joinedload(Pedido.perfil_cliente).joinedload(PerfilCliente.usuario)
            ).order_by(Pedido.fecha_creacion.desc())
            
            if status:
                query = query.filter(Pedido.estado == status)
            
            # Imprimimos la consulta SQL que se va a ejecutar
            print(f"DEBUG (PedidoRoute): Consulta SQL generada:\n{str(query.statement.compile(compile_kwargs={'literal_binds': True}))}\n")
            
            results = query.all()
            
            # Imprimimos la cantidad de resultados obtenidos
            print(f"DEBUG (PedidoRoute): Número de pedidos encontrados: {len(results)}")
            return results

        # La lógica para 'en_espera' se mantiene igual
        pedidos_en_espera = Pedido.query.options(
            joinedload(Pedido.perfil_cliente),
            joinedload(Pedido.detalles)
        ).filter_by(estado='en_espera').all()
        
        print(f"DEBUG (PedidoRoute): Número de pedidos 'en_espera' encontrados: {len(pedidos_en_espera)}")
        
        grupos_de_productos = {}
        for pedido in pedidos_en_espera:
            for detalle in pedido.detalles:
                prod_id = detalle.producto_id
                if not prod_id: continue
                if prod_id not in grupos_de_productos:
                    grupos_de_productos[prod_id] = { "producto_id": prod_id, "nombre_producto": detalle.nombre_producto_historico, "pedidos": [] }
                
                grupos_de_productos[prod_id]["pedidos"].append({
                    "pedido_id": pedido.pedido_id,
                    "detalle_id": detalle.detalle_pedido_id,
                    "cliente_nombre": pedido.perfil_cliente.nombre if pedido.perfil_cliente else "N/A",
                    "cantidad": int((detalle.respuestas_requisitos or {}).get("Cantidad", 1)),
                    "fecha": pedido.fecha_creacion.isoformat(),
                    "respuestas": detalle.respuestas_requisitos,
                    "precio_unitario_historico": float(detalle.precio_unitario_historico or 0),
                    "precio_pagado": float(detalle.precio_pagado or detalle.precio_unitario_historico or 0),
                    "estado": pedido.estado,
                    "fecha_espera_maxima": pedido.fecha_espera_maxima.isoformat() if pedido.fecha_espera_maxima else None
                })
        
        return list(grupos_de_productos.values())
    
    @staticmethod
    def replicate_order(pedido_origen_id: int, perfil_cliente_id: int) -> Optional[Pedido]:
        """Crea un nuevo pedido 'pendiente' como una copia de un pedido anterior."""
        pedido_origen = Pedido.query.get(pedido_origen_id)
        if not pedido_origen:
            return None

        # 1. Cancelar cualquier carrito activo
        carrito_existente = Pedido.query.filter_by(perfil_cliente_id=perfil_cliente_id, estado='pendiente').first()
        if carrito_existente:
            carrito_existente.estado = 'cancelado'
            db.session.commit()

        # 2. Crear el nuevo pedido (el nuevo carrito)
        nuevo_carrito = Pedido(perfil_cliente_id=perfil_cliente_id, estado='pendiente')
        db.session.add(nuevo_carrito)
        db.session.flush() # Para obtener el nuevo pedido_id

        # 3. Copiar los detalles
        for detalle_origen in pedido_origen.detalles:
            nuevo_detalle = DetallePedido(
                pedido_id=nuevo_carrito.pedido_id,
                producto_id=detalle_origen.producto_id,
                respuestas_requisitos=detalle_origen.respuestas_requisitos,
                completo=detalle_origen.completo,
                nombre_producto_historico=detalle_origen.nombre_producto_historico,
                sku_historico=detalle_origen.sku_historico,
                precio_unitario_historico=detalle_origen.precio_unitario_historico
            )
            db.session.add(nuevo_detalle)
        
        db.session.commit()
        return nuevo_carrito
    
    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def calculate_potential_savings(pedido_id: int) -> decimal.Decimal:
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return decimal.Decimal('0.0')

        total_potential_savings = decimal.Decimal('0.0')

        for detalle in pedido.detalles:
            if not detalle.producto_id or not detalle.precio_unitario_historico:
                continue

            all_prices_for_product = PreciosProducto.query.filter_by(producto_id=detalle.producto_id).all()
            if not all_prices_for_product:
                continue
            
            current_variant_full = detalle.respuestas_requisitos or {}
            current_unit_price = detalle.precio_unitario_historico
            
            # --- LÓGICA DE COMPARACIÓN CORREGIDA ---
            variant_prices = []
            for p in all_prices_for_product:
                db_variant = p.variante_requisitos or {}
                # Comprobamos si todos los items de la variante de la BD están en las respuestas del cliente.
                # Esto permite que el cliente tenga respuestas extra (RUT, Dirección) sin que falle la comparación.
                if all(item in current_variant_full.items() for item in db_variant.items()):
                    variant_prices.append(p.precio_unitario)
            
            if not variant_prices:
                continue

            best_possible_unit_price = min(variant_prices)

            if best_possible_unit_price < current_unit_price:
                customer_quantity = int(current_variant_full.get("Cantidad", 1))
                saving_for_item = (current_unit_price - best_possible_unit_price) * customer_quantity
                total_potential_savings += saving_for_item
        
        return total_potential_savings
    
    @staticmethod
    def recalculate_order_total(pedido_id: int):
        """Recalcula el monto total de un pedido basado en sus detalles."""
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            print(f"DEBUG: No se encontró el pedido con ID {pedido_id} para recalcular.")
            return

        print(f"DEBUG: Recalculando total para Pedido ID: {pedido_id}")
        nuevo_total = decimal.Decimal('0.0')
        for detalle in pedido.detalles:
            cantidad_str = (detalle.respuestas_requisitos or {}).get("Cantidad", "1")
            
            # --- PRINT DE DEPURACIÓN ---
            print(f"  > Detalle ID: {detalle.detalle_pedido_id}, Cantidad (str): '{cantidad_str}', Precio Pagado: {detalle.precio_pagado}")

            cantidad = int(cantidad_str)
            precio_final_item = detalle.precio_pagado or detalle.precio_unitario_historico or decimal.Decimal('0.0')
            nuevo_total += (precio_final_item * cantidad)
        
        print(f"DEBUG: Nuevo total calculado: {nuevo_total}")
        pedido.monto_total = nuevo_total
    
    @staticmethod
    def get_full_order_details(pedido_id: int) -> Optional[Pedido]:
        """Obtiene un pedido con todos sus detalles precargados."""
        return Pedido.query.options(
            joinedload(Pedido.detalles)
        ).get(pedido_id)
    
    @staticmethod
    def delete_by_id(pedido_id: int) -> bool:
        """Elimina un pedido y sus detalles (la BD se encarga de la cascada)."""
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            db.session.delete(pedido)
            # El commit se hará en la capa de API.
            return True
        return False
    
    @staticmethod
    def replicate_order_chatbot(pedido_id_origen, perfil_cliente_id):
        """
        Crea un nuevo pedido copiando los detalles de un pedido anterior.
        El nuevo pedido se crea en estado 'esperando_pago'.

        Args:
            pedido_id_origen (int): El ID del pedido que se va a copiar.
            perfil_cliente_id (int): El ID del perfil del cliente que realiza la solicitud.

        Returns:
            Pedido: La nueva instancia del pedido creado.
        """
        from app.models import Pedido, DetallePedido

        pedido_origen = db.session.get(Pedido, pedido_id_origen)
        if not pedido_origen:
            logging.error(f"No se encontró el pedido de origen con ID {pedido_id_origen} para replicar.")
            return None

        # Crear el nuevo pedido
        nuevo_pedido = Pedido(
            perfil_cliente_id=perfil_cliente_id,
            estado='esperando_pago',  # Estado clave para el nuevo flujo
            total_pagado=pedido_origen.total_pagado,
            ahorro_total=pedido_origen.ahorro_total
        )
        db.session.add(nuevo_pedido)
        db.session.flush()  # Para obtener el ID del nuevo pedido

        # Copiar cada detalle del pedido
        for detalle_origen in pedido_origen.detalles:
            nuevo_detalle = DetallePedido(
                pedido_id=nuevo_pedido.pedido_id,
                producto_id=detalle_origen.producto_id,
                cantidad=detalle_origen.cantidad,
                precio_pagado=detalle_origen.precio_pagado,
                nombre_historico=detalle_origen.nombre_historico,
                sku_historico=detalle_origen.sku_historico,
                respuestas_requisitos=detalle_origen.respuestas_requisitos,
                completo=True
            )
            db.session.add(nuevo_detalle)

        db.session.commit()
        logging.info(f"Pedido {pedido_id_origen} replicado exitosamente en el nuevo pedido {nuevo_pedido.pedido_id}.")
        return nuevo_pedido


    