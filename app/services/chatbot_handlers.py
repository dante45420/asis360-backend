# app/services/chatbot_handlers.py

from .chatbot_actions import ChatbotActions
from app.routes import PerfilClienteRoute

class BotHandlers:

    @staticmethod
    def handle_solicitando_nombre(profile, conversation, user_input):
        """Recibe el nombre del usuario y pide confirmación."""
        if isinstance(user_input, str) and len(user_input) > 2:
            # En lugar de guardar directamente, pide confirmación
            return ChatbotActions.request_name_confirmation(profile, conversation, user_input)
        else:
            # Si no envía un nombre válido, se lo volvemos a pedir
            return ChatbotActions.request_name(profile, conversation)
    
    @staticmethod
    def handle_esperando_confirmacion_nombre(profile, conversation, user_input):
        """Procesa la confirmación del nombre."""
        if user_input == 'confirm_name_yes':
            # Si es correcto, movemos el nombre de pendiente a definitivo
            PerfilClienteRoute.update_by_id(
                profile.perfil_cliente_id, 
                {'nombre': profile.nombre_pendiente, 'nombre_pendiente': None}
            )
            # Obtenemos el perfil actualizado para el saludo
            updated_profile = PerfilClienteRoute.get_by_id(profile.perfil_cliente_id)
            # Y le mostramos el menú principal
            return ChatbotActions.send_main_menu(updated_profile, conversation)
        
        elif user_input == 'confirm_name_no':
            # Si no es correcto, borramos el nombre pendiente y lo pedimos de nuevo
            PerfilClienteRoute.update_by_id(profile.perfil_cliente_id, {'nombre_pendiente': None})
            return ChatbotActions.request_name(profile, conversation)
        else:
            # Si responde otra cosa, le volvemos a mostrar la confirmación
            return ChatbotActions.request_name_confirmation(profile, conversation, profile.nombre_pendiente)

    @staticmethod
    def handle_inicio(profile, conversation, user_input):
        """Punto de entrada: pide el nombre si es nuevo, o muestra el menú si ya lo conoce."""
        if not profile.nombre:
            return ChatbotActions.request_name(profile, conversation)
        else:
            return ChatbotActions.send_main_menu(profile, conversation)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def handle_esperando_opcion_menu(profile, conversation, user_input):
        """Procesa la elección del usuario en el menú principal."""
        if user_input == 'info_menu':
            return ChatbotActions.send_info_menu(profile, conversation)
        elif user_input == 'create_order_bot':
            return ChatbotActions.request_order_description(profile, conversation)
        # --- NUEVA LÓGICA AÑADIDA ---
        elif user_input == 'talk_to_human':
            return ChatbotActions.escalate_to_human(profile, conversation)
        else:
            # Si el usuario escribe algo inválido, le mostramos el menú de nuevo
            return ChatbotActions.send_main_menu(profile, conversation)


    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def handle_esperando_tipo_info(profile, conversation, user_input):
        """Procesa la elección del sub-menú de información."""
        if user_input == 'info_cafeteria':
            return ChatbotActions.send_info_for_cafeterias(profile, conversation)
        elif user_input == 'info_proveedor':
            return ChatbotActions.send_info_for_proveedores(profile, conversation)
        else:
            # Si no elige una opción válida, le volvemos a preguntar
            return ChatbotActions.send_info_menu(profile, conversation)

    # --- NUEVA FUNCIÓN ---
    @staticmethod
    def handle_esperando_descripcion_pedido(profile, conversation, user_input):
        """Recibe la descripción del pedido, crea el ticket y confirma."""
        if isinstance(user_input, str) and len(user_input) > 10:
            # Asumimos que una descripción de más de 10 caracteres es válida
            return ChatbotActions.create_ticket_and_confirm(profile, conversation, user_input)
        else:
            # Si el mensaje es muy corto, le pedimos que sea más descriptivo
            return ChatbotActions.request_order_description(profile, conversation)