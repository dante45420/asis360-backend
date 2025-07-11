# app/services/whatsapp_message_builder.py

from app.services.content_formatter import ContentFormatter

class WhatsappMessageBuilder:

    @staticmethod
    def build_text_message(phone_number, text):
        """Construye un mensaje de texto simple."""
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": ContentFormatter.truncate(text, 4096)}
        }

    @staticmethod
    def build_simplified_main_menu(phone_number, header_text):
        """Construye el menú principal simplificado con 3 botones."""
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": ContentFormatter.truncate(header_text, 60)
                },
                "body": {
                    "text": "Por favor, elige una de las siguientes opciones:"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "create_order",
                                "title": "📝 Crear Pedido"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "view_orders",
                                "title": "🛍️ Ver mis Pedidos"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "talk_to_human",
                                "title": "🗣️ Hablar con Asesor"
                            }
                        }
                    ]
                }
            }
        }

    @staticmethod
    def build_recent_orders_list(phone_number, pedidos):
        """Construye una lista interactiva con los pedidos recientes."""
        rows = []
        for pedido in pedidos:
            # Formatear la fecha para que sea más legible
            fecha_pedido = pedido.fecha_creacion.strftime('%d de %b, %Y')
            total_str = f"${int(pedido.total_pagado):,}".replace(",", ".")
            
            rows.append({
                "id": f"repeat_order_{pedido.pedido_id}",
                "title": f"Pedido #{pedido.pedido_id}",
                "description": ContentFormatter.truncate(f"Fecha: {fecha_pedido} - Total: {total_str}", 72)
            })

        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": "Tus Pedidos Recientes"
                },
                "body": {
                    "text": "Aquí están tus últimos 5 pedidos. Selecciona uno si deseas repetirlo."
                },
                "action": {
                    "button": "Ver Pedidos",
                    "sections": [
                        {
                            "title": "Historial de Pedidos",
                            "rows": rows
                        }
                    ]
                }
            }
        }
    
    @staticmethod
    def build_support_session_ended_message(phone_number):
        """Construye un mensaje para notificar que la sesión de soporte ha terminado."""
        texto = "Un asesor ha marcado esta conversación como resuelta. Si tienes otra consulta, no dudes en escribirnos de nuevo."
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": texto}
        }
    
    @staticmethod
    def build_verification_code_message(phone_number, verification_code):
        """Construye el mensaje para enviar un código de verificación."""
        texto = (
            f"¡Hola! Para verificar que esta cuenta te pertenece, por favor usa el siguiente código en la página de registro:\n\n"
            f"**Código de Verificación:** `{verification_code}`\n\n"
            "Este código es válido por 10 minutos."
        )
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": texto}
        }
    
    # --- NUEVA FUNCIÓN ---
    # --- FUNCIÓN MODIFICADA ---
    @staticmethod
    def build_main_menu(phone_number, user_name):
        """Construye el menú principal con las 3 opciones clave."""
        header_text = f"¡Hola, {user_name}! ¿Cómo puedo ayudarte hoy?"
        body_text = "Por favor, elige una de las siguientes opciones:"
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"type": "text", "text": ContentFormatter.truncate(header_text, 60)},
                "body": {"text": ContentFormatter.truncate(body_text, 1024)},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "info_menu", "title": "ℹ️ Información"}},
                        {"type": "reply", "reply": {"id": "create_order_bot", "title": "📝 Crear Pedido"}},
                        # --- NUEVO BOTÓN AÑADIDO ---
                        {"type": "reply", "reply": {"id": "talk_to_human", "title": "🗣️ Hablar con Asesor"}}
                    ]
                }
            }
        }

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def build_info_menu(phone_number):
        """Construye el menú para que el usuario elija su perfil (cafetería o proveedor)."""
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "Claro, ¿qué tipo de información te gustaría recibir?"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "info_cafeteria", "title": "Soy una Cafetería"}},
                        {"type": "reply", "reply": {"id": "info_proveedor", "title": "Soy un Proveedor"}}
                    ]
                }
            }
        }

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def build_request_order_description_message(phone_number):
        """Construye el mensaje que pide al usuario describir su pedido."""
        texto = (
            "¡Perfecto! Por favor, escribe en **un solo mensaje** todo lo que necesitas, "
            "siendo lo más descriptivo posible (producto, cantidad, marca, etc.).\n\n"
            "Ejemplo: 'Necesito 2 cajas de leche Soprole entera y 3kg de café de grano de Colombia'."
        )
        return WhatsappMessageBuilder.build_text_message(phone_number, texto)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def build_order_created_confirmation_message(phone_number):
        """Construye el mensaje de confirmación tras crear el ticket de pedido."""
        texto = (
            "¡Recibido! ✅ Hemos registrado tu solicitud.\n\n"
            "Un asesor revisará tu pedido y se pondrá en contacto contigo por este mismo chat para confirmar los detalles y el pago. ¡Gracias!"
        )
        return WhatsappMessageBuilder.build_text_message(phone_number, texto)
    
    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def build_name_confirmation_message(phone_number, pending_name):
        """Construye el mensaje para confirmar el nombre del usuario."""
        body_text = f"¡Perfecto! Para confirmar, tu nombre es *{pending_name}*, ¿correcto?"
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "confirm_name_yes", "title": "Sí, es correcto"}},
                        {"type": "reply", "reply": {"id": "confirm_name_no", "title": "No, es otro"}}
                    ]
                }
            }
        }
    
    @staticmethod
    def build_cafeteria_info_sequence(phone_number):
        """
        Construye una secuencia de mensajes informativos para cafeterías.
        Devuelve una LISTA de payloads de mensajes.
        """
        summary = (
            "¡Somos tu nuevo socio estratégico! 🤝\n\n"
            "Somos una plataforma que centraliza y optimiza todas las compras de tu cafetería. "
            "Olvídate de llamar a múltiples proveedores y de perder tiempo en cotizaciones. ¡Nosotros lo hacemos por ti!"
        )

        ahorro = (
            "*Pilar 1: Ahorro de Tiempo y Dinero* 💰\n\n"
            "✅ *Mejores Precios:* Compramos en grandes volúmenes junto a otras cafeterías, consiguiendo precios que no podrías obtener por tu cuenta.\n"
            "✅ *Todo Pre-Cotizado:* Ahorra horas de gestión. Todos nuestros productos ya tienen los mejores precios negociados para ti."
        )

        control = (
            "*Pilar 2: Control Total* 📊\n\n"
            "✅ *Un Solo Pago:* Centraliza todos tus gastos en una sola boleta o factura al final del mes.\n"
            "✅ *Visibilidad Completa:* Accede a un panel web para ver tu historial de compras y controlar tus gastos fácilmente."
        )
        
        confianza = (
            "*Pilar 3: Confianza y Soporte* ⭐\n\n"
            "✅ *Proveedores Verificados:* Solo trabajamos con los mejores proveedores, calificados por otras cafeterías como la tuya.\n"
            "✅ *Soporte de Calidad:* Si tienes un problema, hablamos directamente con el proveedor por ti. Tu tranquilidad es nuestra prioridad."
        )

        # Se retorna una lista de mensajes a enviar en secuencia
        return [
            WhatsappMessageBuilder.build_text_message(phone_number, summary),
            WhatsappMessageBuilder.build_text_message(phone_number, ahorro),
            WhatsappMessageBuilder.build_text_message(phone_number, control),
            WhatsappMessageBuilder.build_text_message(phone_number, confianza),
        ]

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def build_proveedor_info_sequence(phone_number):
        """
        Construye una secuencia de mensajes profesionales para proveedores.
        Devuelve una LISTA de payloads de mensajes.
        """
        summary = (
            "*Propuesta de Valor para Proveedores*\n\n"
            "Somos una plataforma B2B que actúa como un socio estratégico para tu negocio, "
            "optimizando tu canal de ventas y conectándote con una red de compradores calificados (cafeterías de especialidad) de forma eficiente y segura."
        )

        beneficios_1 = (
            "*Beneficios Operacionales y Financieros*\n\n"
            "1. *Logística Simplificada:*\nRecibe una única Orden de Compra consolidada en lugar de gestionar múltiples pedidos pequeños. Esto se traduce en menos administración y mayor eficiencia.\n\n"
            "2. *Cobranza Garantizada y Puntual:*\nElimina el riesgo y el esfuerzo de la cobranza. Nosotros gestionamos los pagos de los clientes y te aseguramos una transferencia puntual y centralizada."
        )

        beneficios_2 = (
            "*Beneficios Estratégicos y Comerciales*\n\n"
            "3. *Relación Estratégica a Largo Plazo:*\nMás que un simple canal, buscamos ser un socio. Nos dedicamos a entender tu negocio para crear una alianza duradera y beneficiosa.\n\n"
            "4. *Inteligencia de Mercado:*\nAccede a datos agregados sobre los productos más demandados y las tendencias del sector para optimizar tu inventario y estrategia de ventas."
        )

        como_funciona = (
            "*¿Cómo trabajar con nosotros?*\n\n"
            "Nuestro proceso se basa en la confianza y la colaboración:\n"
            "1. *Conversación Inicial:* Nos reunimos para conocer tu empresa y productos.\n"
            "2. *Acuerdo Comercial:* Definimos juntos los términos de nuestra alianza.\n"
            "3. *Integración:* Te damos la bienvenida a nuestra red y comienzas a recibir pedidos consolidados.\n\n"
            "Si te interesa, un asesor puede contactarte para iniciar el proceso."
        )

        return [
            WhatsappMessageBuilder.build_text_message(phone_number, summary),
            WhatsappMessageBuilder.build_text_message(phone_number, beneficios_1),
            WhatsappMessageBuilder.build_text_message(phone_number, beneficios_2),
            WhatsappMessageBuilder.build_text_message(phone_number, como_funciona),
        ]
