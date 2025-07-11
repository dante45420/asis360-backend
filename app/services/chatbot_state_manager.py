# app/services/chatbot_state_manager.py

import logging
from .chatbot_config import STATE_CONFIG
from .chatbot_handlers import BotHandlers
from app.routes import MensajeRoute
from . chatbot_actions import ChatbotActions

class ChatbotStateManager:
    @staticmethod
    def manage_conversation_state(profile, conversation, user_input):
        """
        Gestiona la lógica de la máquina de estados.
        MODIFICADO: Ahora puede procesar y enviar una lista de mensajes.
        """
        from .whatsapp_api_client import WhatsAppApiClient

        if profile.bot_pausado:
            logging.info(f"El bot está en pausa para el perfil {profile.perfil_cliente_id}. No se procesa el mensaje.")
            return

        current_state = conversation.estado_actual
        state_info = STATE_CONFIG.get(current_state)
        
        if not state_info:
            logging.error(f"Estado desconocido '{current_state}'. Escalando a un asesor.")
            # Aseguramos que la respuesta sea una lista para mantener la consistencia
            messages_to_send = [ChatbotActions.escalate_to_human(profile, conversation, "He encontrado una situación inesperada.")]
        else:
            handler_function = state_info.get('handler')
            if not callable(handler_function):
                logging.error(f"No se encontró un 'handler' válido para el estado '{current_state}'.")
                messages_to_send = [ChatbotActions.escalate_to_human(profile, conversation)]
            else:
                logging.info(f"--- [State Manager] --- Estado: '{current_state}' | Input: {user_input}")
                try:
                    # El handler ahora puede devolver un único mensaje (dict) o una lista de mensajes (list)
                    response = handler_function(profile, conversation, user_input)
                    # Nos aseguramos de que messages_to_send siempre sea una lista
                    messages_to_send = response if isinstance(response, list) else [response]
                except Exception as e:
                    logging.critical(f"Error crítico al ejecutar el handler para '{current_state}': {e}", exc_info=True)
                    messages_to_send = [ChatbotActions.escalate_to_human(profile, conversation, "Lo siento, ocurrió un error interno.")]
        
        # Centralizamos el envío de mensajes, iterando sobre la lista
        for message in messages_to_send:
            if message:
                WhatsAppApiClient.send_message(message)
                text_to_log = message.get('text', {}).get('body', 'Mensaje interactivo enviado')
                MensajeRoute.create_bot_message(conversation.conversacion_id, text_to_log)