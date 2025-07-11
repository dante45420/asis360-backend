# app/api/auth_routes.py

from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from app.routes import UsuarioRoute, PerfilClienteRoute
from app.models import Usuario
from app.services.whatsapp_message_builder import WhatsappMessageBuilder
from app.services.whatsapp_api_client import WhatsAppApiClient
import logging
import random
import re

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def normalize_phone_number(phone: str) -> str:
    """
    Normaliza un número de teléfono chileno al formato '569...'.
    Ejemplos:
    - 969172764 -> 56969172764
    - +56969172764 -> 56969172764
    """
    if not phone or not isinstance(phone, str):
        return ""
    
    # Eliminar caracteres no numéricos, excepto el '+' inicial
    cleaned_phone = re.sub(r'[^\d+]', '', phone)

    if cleaned_phone.startswith('+569') and len(cleaned_phone) == 12:
        return cleaned_phone[1:] # Quita el '+'
    elif cleaned_phone.startswith('569') and len(cleaned_phone) == 11:
        return cleaned_phone # Ya está en el formato correcto
    elif cleaned_phone.startswith('9') and len(cleaned_phone) == 9:
        return f"56{cleaned_phone}" # Añade el prefijo 56
    
    # Si no coincide con ningún formato conocido, devuelve el número limpiado
    return cleaned_phone


bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# --- Ruta de Login ---
@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email y contraseña son requeridos"}), 400

    email = data['email'].lower()
    password = data['password']
    user = UsuarioRoute.find_by_email(email)

    if not user or not user.check_password(password):
        return jsonify({"message": "Credenciales inválidas"}), 401
    
    token = jwt.encode({
        'sub': str(user.usuario_id),
        'rol': user.rol,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "token": token,
        "user": {"nombre": user.nombre, "email": user.email, "rol": user.rol}
    }), 200

# --- Ruta de Registro ---
@bp.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    required_fields = ['nombre', 'email', 'password', 'telefono']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Faltan datos para el registro."}), 400

    email = data['email'].lower()
    telefono = normalize_phone_number(data['telefono'])

    if UsuarioRoute.find_by_email(email):
        return jsonify({"message": "Este email ya está registrado."}), 409
    
    perfil_existente = PerfilClienteRoute.get_by_phone(telefono)
    if perfil_existente and perfil_existente.usuario_id is not None:
         return jsonify({"message": "Este número de teléfono ya está vinculado a otra cuenta."}), 409

    if perfil_existente:
        # El usuario ya chateó. Enviar código de verificación.
        try:
            codigo = str(random.randint(100000, 999999))
            PerfilClienteRoute.update_by_id(perfil_existente.perfil_cliente_id, {
                'codigo_verificacion': codigo,
                'codigo_expiracion': datetime.utcnow() + timedelta(minutes=10)
            })
            message_payload = WhatsappMessageBuilder.build_verification_code_message(telefono, codigo)
            WhatsAppApiClient.send_message(message_payload)
            
            # --- CORRECCIÓN FINAL Y DEFINITIVA ---
            # Devolvemos el código 202 para que el frontend lo interprete como "verificación requerida"
            print("DEBUG BACKEND: Devolviendo respuesta de VERIFICACIÓN con código 202")
            return jsonify({
                "message": "Este número ya está en nuestro chat. Te hemos enviado un código de verificación por WhatsApp para vincular tu cuenta.",
                "requires_verification": True
            }), 202 # <--- ESTE ES EL CÓDIGO DE ESTADO CORRECTO

        except Exception as e:
            logging.error(f"ERROR: No se pudo enviar código de verificación: {e}", exc_info=True)
            return jsonify({"message": "No pudimos enviar el código de verificación."}), 500
    
    else:
        # Usuario completamente nuevo. Se registra directamente.
        try:
            nuevo_usuario = UsuarioRoute.create_with_profile(
                nombre=data['nombre'], email=email, password=data['password'], telefono=telefono
            )
            if not nuevo_usuario:
                 raise Exception("La creación del usuario con perfil falló.")

            

            token = jwt.encode({
                'sub': str(nuevo_usuario.usuario_id),
                'rol': nuevo_usuario.rol,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")

            # El código 201 es correcto para una creación exitosa.
            return jsonify({
                "message": "Usuario registrado exitosamente.",
                "token": token,
                "user": {"nombre": nuevo_usuario.nombre, "email": nuevo_usuario.email, "rol": nuevo_usuario.rol}
            }), 201
        
        except Exception as e:
            logging.error(f"Error al crear nuevo usuario y perfil: {e}", exc_info=True)
            return jsonify({"message": "Error interno al registrar el usuario."}), 500


# --- Ruta de Verificación ---
@bp.route('/verificar', methods=['POST'])
def verificar_codigo():
    data = request.get_json()
    required_fields = ['nombre', 'email', 'password', 'telefono', 'codigo']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Faltan datos para la verificación."}), 400

    telefono = normalize_phone_number(data['telefono'])
    codigo_usuario = data['codigo']

    perfil = PerfilClienteRoute.get_by_phone(telefono)

    if not perfil or not perfil.codigo_verificacion:
        return jsonify({"message": "No hay una verificación pendiente para este número."}), 404

    if perfil.codigo_expiracion < datetime.utcnow():
        return jsonify({"message": "El código de verificación ha expirado."}), 400
    
    if perfil.codigo_verificacion != codigo_usuario:
        return jsonify({"message": "El código de verificación es incorrecto."}), 400

    try:
        nuevo_usuario = UsuarioRoute.create(
             nombre=data['nombre'], email=data['email'].lower(), password=data['password'], telefono=telefono
        )
        if not nuevo_usuario:
            raise Exception("Falló la creación del usuario durante la verificación.")

        PerfilClienteRoute.update_by_id(perfil.perfil_cliente_id, {
            'usuario_id': nuevo_usuario.usuario_id,
            'nombre': nuevo_usuario.nombre,
            'codigo_verificacion': None,
            'codigo_expiracion': None
        })
        
        token = jwt.encode({
            'sub': str(nuevo_usuario.usuario_id),
            'rol': nuevo_usuario.rol,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            "message": "Cuenta verificada y registrada exitosamente.",
            "token": token,
            "user": {"nombre": nuevo_usuario.nombre, "email": nuevo_usuario.email, "rol": nuevo_usuario.rol}
        }), 200

    except Exception as e:
        logging.error(f"Error al crear usuario tras verificación: {e}", exc_info=True)
        return jsonify({"message": "Error interno al finalizar el registro."}), 500
