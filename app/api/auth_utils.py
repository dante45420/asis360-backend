# app/api/auth_utils.py
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from app.routes.usuario_routes import UsuarioRoute # Usaremos la ruta para ser consistentes

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # --- CORRECCIÓN PARA TypeError en OPTIONS ---
        # Si la petición es OPTIONS, devolvemos una respuesta OK inmediatamente.
        # El navegador solo necesita la confirmación de CORS, no la ejecución de la lógica.
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        token = None
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer '):
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Falta el token de autorización'}), 401
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # --- CORRECCIÓN PARA KeyError: 'usuario_id' ---
            # Usamos 'sub' para obtener el ID del usuario, que es el estándar y como se genera el token.
            current_user = UsuarioRoute.get_by_id(int(data['sub']))
            
            if not current_user:
                return jsonify({'message': 'El usuario del token no existe'}), 401
            
            # g.current_user = current_user # 'g' es útil pero no lo estamos usando, se puede omitir por ahora.

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'El token ha expirado'}), 401
        except Exception as e:
            current_app.logger.error(f"Error en la validación del token: {e}")
            return jsonify({'message': 'Token inválido o error al procesarlo'}), 401
            
        # Pasamos el usuario encontrado a la función del endpoint
        return f(current_user, *args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.rol != 'admin':
            return jsonify({'message': 'Acceso denegado: se requiere rol de administrador'}), 403
        return f(current_user, *args, **kwargs)
    return decorated