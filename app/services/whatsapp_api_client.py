# app/services/whatsapp_api_client.py
import requests
import json
from flask import current_app

class WhatsAppApiClient:
    """
    Cliente centralizado para interactuar con la API de WhatsApp Business.
    """
    
    @staticmethod
    def send_message(payload: dict):
        """
        Método principal y genérico que toma un payload completo y lo envía a la API.
        """
        token = current_app.config.get('WHATSAPP_TOKEN')
        phone_number_id = current_app.config.get('PHONE_NUMBER_ID')
        
        if not token or not phone_number_id:
            print("[API_CLIENT ERROR] Faltan WHATSAPP_TOKEN o PHONE_NUMBER_ID en la configuración.")
            return None

        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            print(f"[API_CLIENT] Mensaje enviado a {payload.get('to')}. Respuesta: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"!!!!!!!!!! [API_CLIENT ERROR] !!!!!!!!!!!")
            print(f"Error al enviar payload a la API de WhatsApp: {e}")
            if e.response is not None:
                print(f"Respuesta del servidor ({e.response.status_code}): {e.response.text}")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return None

    @staticmethod
    def send_text_message(phone_number: str, text: str):
        """
        Atajo para enviar mensajes de texto simples. Usado por auth_routes, etc.
        """
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'text',
            'text': {'body': text}
        }
        return WhatsAppApiClient.send_message(payload)