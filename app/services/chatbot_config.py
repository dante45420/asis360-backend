# app/services/chatbot_config.py

from .chatbot_handlers import BotHandlers

STATE_CONFIG = {
    'solicitando_nombre': {
        'handler': BotHandlers.handle_solicitando_nombre,
    },
    # --- NUEVO ESTADO AÑADIDO ---
    'esperando_confirmacion_nombre': {
        'handler': BotHandlers.handle_esperando_confirmacion_nombre,
    },
    'inicio': {
        'handler': BotHandlers.handle_inicio,
    },
    'esperando_opcion_menu': {
        'handler': BotHandlers.handle_esperando_opcion_menu,
    },
    'esperando_tipo_info': {
        'handler': BotHandlers.handle_esperando_tipo_info,
    },
    'esperando_descripcion_pedido': {
        'handler': BotHandlers.handle_esperando_descripcion_pedido,
    },
}