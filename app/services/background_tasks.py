# app/services/background_tasks.py
import time
from flask import current_app
from app.routes import ConversacionRoute
from app.services.whatsapp_api_client import WhatsAppApiClient
from app.services.whatsapp_message_builder import WhatsappMessageBuilder

def check_inactive_conversations_job(app):
    """
    Esta es la función que se ejecuta en un hilo en segundo plano.
    Revisa y cierra conversaciones inactivas a intervalos regulares.
    """
    print(">> HILO SECUNDARIO: Iniciado. La primera revisión ocurrirá en unos minutos...")
    
    time.sleep(60) # Espera inicial de 1 minuto

    while True:
        intervalo_minutos = 5 # Valor por defecto si falla la config
        try:
            with app.app_context():
                # Obtenemos los valores de configuración DENTRO del contexto.
                intervalo_minutos = int(current_app.config.get('TIMEOUT_CHECK_INTERVAL_MINUTES', 5))
                timeout_minutos = int(current_app.config.get('CONVERSATION_TIMEOUT_MINUTES', 60))
                
                print(f">> HILO SECUNDARIO: Despertando para revisar conversaciones inactivas (timeout > {timeout_minutos} min)...")
                
                # 1. Obtenemos la lista de conversaciones que se cerraron.
                conversaciones_cerradas = ConversacionRoute.end_inactive_conversations(timeout_minutes=timeout_minutos)
                
                if conversaciones_cerradas:
                    print(f">> HILO SECUNDARIO: Se cerraron {len(conversaciones_cerradas)} conversaciones por inactividad.")
                    
                    # 2. Preparamos el mensaje de despedida una sola vez.
                    mensaje_despedida = WhatsappMessageBuilder.get_farewell_message()

                    # 3. Iteramos sobre la lista para notificar a cada cliente.
                    for conv in conversaciones_cerradas:
                        # --- CORRECCIÓN CLAVE ---
                        # Lógica segura para obtener el teléfono y notificar
                        if conv.perfil_cliente and conv.perfil_cliente.telefono_vinculado:
                            print(f"   -> Enviando mensaje de cierre a {conv.perfil_cliente.telefono_vinculado}")
                            WhatsAppApiClient.send_message(conv.perfil_cliente.telefono_vinculado, mensaje_despedida)
                else:
                    print(">> HILO SECUNDARIO: No se encontraron conversaciones inactivas para cerrar.")

        except Exception as e:
            print(f"ERROR en el hilo de tareas en segundo plano: {repr(e)}")
        
        # El hilo duerme fuera del contexto de la aplicación.
        print(f">> HILO SECUNDARIO: Durmiendo por {intervalo_minutos} minutos...")
        time.sleep(intervalo_minutos * 60)