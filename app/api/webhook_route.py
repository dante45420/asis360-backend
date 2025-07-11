# app/api/webhook_route.py

from flask import Blueprint, request, jsonify, current_app
from app.services import whatsapp_service 

bp = Blueprint('webhook', __name__, url_prefix='/')

@bp.route('/webhook', methods=['GET', 'POST'])
def webhook_handler():
    if request.method == 'GET':
        # ... (código de verificación sin cambios)
        verify_token = current_app.config['VERIFY_TOKEN']
        if request.args.get('hub.verify_token') == verify_token:
            return request.args.get('hub.challenge', ''), 200
        else:
            return 'Error, token de verificación no válido', 403

    if request.method == 'POST':
        data = request.get_json()
        # Delegamos TODO el procesamiento al nuevo punto de entrada del servicio
        whatsapp_service.process_webhook_data(data)
        return jsonify({'status': 'ok'}), 200