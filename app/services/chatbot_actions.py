# app/services/chatbot_actions.py

import logging
from app.routes import ConversacionRoute, PerfilClienteRoute
from app.services.whatsapp_message_builder import WhatsappMessageBuilder
# --- NUEVA IMPORTACIÓN ---
from app.routes.ticket_producto_routes import TicketProductoRoute 

class ChatbotActions:

    @staticmethod
    def request_name(profile, conversation):
        """Prepara el mensaje para solicitar el nombre."""
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'solicitando_nombre')
        return WhatsappMessageBuilder.build_text_message(
            profile.telefono_vinculado,
            "¡Hola! 👋 Soy tu asistente de compras virtual. Para comenzar, ¿podrías indicarme tu nombre completo?"
        )
    
    @staticmethod
    def request_name_confirmation(profile, conversation, temp_name):
        """Guarda el nombre temporalmente y pide confirmación."""
        # Guardamos el nombre en el campo pendiente
        PerfilClienteRoute.update_by_id(profile.perfil_cliente_id, {'nombre_pendiente': temp_name})
        # Cambiamos el estado para esperar la confirmación
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'esperando_confirmacion_nombre')
        return WhatsappMessageBuilder.build_name_confirmation_message(profile.telefono_vinculado, temp_name)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def send_main_menu(profile, conversation):
        """Envía el menú principal al usuario."""
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'esperando_opcion_menu')
        return WhatsappMessageBuilder.build_main_menu(profile.telefono_vinculado, profile.nombre)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def send_info_menu(profile, conversation):
        """Envía el sub-menú de información."""
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'esperando_tipo_info')
        return WhatsappMessageBuilder.build_info_menu(profile.telefono_vinculado)

    @staticmethod
    def send_info_for_cafeterias(profile, conversation):
        """
        Prepara la secuencia de mensajes para cafeterías y resetea la conversación.
        Ahora devuelve una LISTA de mensajes.
        """
        # Reinicia el estado para la próxima interacción que tenga el usuario
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'inicio')
        # Devuelve la secuencia completa de mensajes
        return WhatsappMessageBuilder.build_cafeteria_info_sequence(profile.telefono_vinculado)

    # --- FUNCIÓN MODIFICADA ---
    @staticmethod
    def send_info_for_proveedores(profile, conversation):
        """
        Prepara la secuencia de mensajes para proveedores y resetea la conversación.
        Ahora devuelve una LISTA de mensajes.
        """
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'inicio')
        return WhatsappMessageBuilder.build_proveedor_info_sequence(profile.telefono_vinculado)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def request_order_description(profile, conversation):
        """Pide al usuario que describa su pedido."""
        ConversacionRoute.update_conversation_state(conversation.conversacion_id, 'esperando_descripcion_pedido')
        return WhatsappMessageBuilder.build_request_order_description_message(profile.telefono_vinculado)
    
    # --- NUEVA FUNCIÓN ---
    # --- FUNCIÓN MODIFICADA ---
    # Ahora create_ticket_and_confirm utiliza la nueva acción centralizada
    @staticmethod
    def create_ticket_and_confirm(profile, conversation, order_description):
        """Crea el ticket, confirma al usuario y escala a un asesor."""
        TicketProductoRoute.crear_ticket_de_pedido_bot(
            perfil_cliente_id=profile.perfil_cliente_id,
            descripcion_pedido=order_description
        )
        
        # Se reutiliza la acción de escalado
        ChatbotActions.escalate_to_human(profile, conversation)
        
        # Se envía el mensaje de confirmación por separado
        return WhatsappMessageBuilder.build_order_created_confirmation_message(profile.telefono_vinculado)


    @staticmethod
    def greet_and_escalate(profile, conversation):
        """Saluda y escala a un humano (ahora usado principalmente para nuevos usuarios)."""
        PerfilClienteRoute.update_by_id(profile.perfil_cliente_id, {'bot_pausado': True})
        ConversacionRoute.update_support_state(conversation.conversacion_id, 'pendiente')
        texto_saludo = f"¡Muchas gracias, {profile.nombre}! Hemos guardado tu nombre."
        texto_escalamiento = "Un asesor humano se pondrá en contacto contigo en breve por este mismo chat. ¡Gracias por tu paciencia!"
        mensaje_final = f"{texto_saludo}\n\n{texto_escalamiento}"
        logging.info(f"Conversación {conversation.conversacion_id} escalada para el nuevo perfil {profile.perfil_cliente_id}.")
        return WhatsappMessageBuilder.build_text_message(profile.telefono_vinculado, mensaje_final)
    
    @staticmethod
    def escalate_to_human(profile, conversation):
        """
        Pausa el bot, marca la conversación para un asesor y notifica al usuario.
        Esta es la acción central para escalar a un humano.
        """
        # Pausar el bot para este PERFIL DE CLIENTE
        PerfilClienteRoute.update_by_id(profile.perfil_cliente_id, {'bot_pausado': True})
        # Marcar la CONVERSACIÓN para que un asesor la atienda
        ConversacionRoute.update_support_state(conversation.conversacion_id, 'pendiente')

        texto_escalamiento = "¡Entendido! Un asesor humano se pondrá en contacto contigo en breve por este mismo chat. Gracias por tu paciencia."
        
        logging.info(f"Conversación {conversation.conversacion_id} escalada a un asesor para el perfil {profile.perfil_cliente_id}.")
        
        return WhatsappMessageBuilder.build_text_message(
            profile.telefono_vinculado,
            texto_escalamiento
        )
