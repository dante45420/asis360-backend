# app/services/whatsapp_service.py

import logging
from app.routes import PerfilClienteRoute, ConversacionRoute, MensajeRoute
from .chatbot_state_manager import ChatbotStateManager

def process_webhook_data(data: dict):
    """
    Punto de entrada principal para procesar los webhooks de WhatsApp.
    """
    try:
        changes = data.get('entry', [])[0].get('changes', [])
        if not changes or 'messages' not in changes[0].get('value', {}):
            return

        message_data = changes[0]['value']['messages'][0]
        wa_id = message_data['from']
        wam_id = message_data['id']
        message_type = message_data.get('type')

        if MensajeRoute.wam_id_exists(wam_id):
            return

        profile = PerfilClienteRoute.get_by_phone(wa_id)
        if not profile:
            profile = PerfilClienteRoute.create(phone_number=wa_id)
            logging.info(f"Nuevo perfil de cliente creado para: {wa_id}")

        conversation = ConversacionRoute.get_active_conversation(profile.perfil_cliente_id)
        if not conversation:
            conversation = ConversacionRoute.create_new_conversation(profile.perfil_cliente_id)
            logging.info(f"Nueva conversación (ID: {conversation.conversacion_id}) iniciada.")

        # --- LÓGICA CORREGIDA PARA LEER LA RESPUESTA DEL USUARIO ---
        user_input = ""
        if message_type == 'interactive':
            # Si es un botón, el input es el ID del botón presionado
            user_input = message_data.get('interactive', {}).get('button_reply', {}).get('id', '')
        elif message_type == 'text':
            # Si es texto, el input es el cuerpo del mensaje
            user_input = message_data.get('text', {}).get('body', '')
        
        # Si no hay un input válido, no continuamos
        if not user_input:
            logging.warning("No se pudo extraer un input válido del mensaje.")
            return
            
        message_to_log = user_input if message_type == 'text' else f"Botón presionado: {user_input}"
        MensajeRoute.registrar_mensaje_usuario(
            conversacion_id=conversation.conversacion_id,
            wam_id=wam_id,
            tipo_mensaje=message_type,
            cuerpo_mensaje=message_to_log
        )
        
        logging.info(f"Mensaje de '{wa_id}' procesado. Contenido: '{message_to_log}'")

        ChatbotStateManager.manage_conversation_state(profile, conversation, user_input)

    except Exception as e:
        logging.critical(f"Error inesperado en el procesamiento del webhook: {e}", exc_info=True)