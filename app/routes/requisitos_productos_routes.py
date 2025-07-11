# app/routes/requisitos_productos_routes.py

import re
from app import db
from app.models.requisito_producto_model import RequisitoProducto
from typing import Optional, List

class RequisitoProductoRoute:
    """
    Gestiona las operaciones de la base de datos para la entidad RequisitoProducto.
    """

    @staticmethod
    def validate_input(texto_usuario: str, tipo_validacion: str) -> bool:
        """
        Punto de entrada principal para validar. Delega a la función correcta.
        """
        if tipo_validacion == 'email':
            return RequisitoProductoRoute._is_valid_email(texto_usuario)
        elif tipo_validacion == 'rut_chileno':
            return RequisitoProductoRoute._is_valid_rut(texto_usuario)
        elif tipo_validacion == 'numero':
            return RequisitoProductoRoute._is_valid_number(texto_usuario)
        elif tipo_validacion == 'texto_simple':
            return True # Siempre es válido
        else:
            # Si el tipo de validación no se reconoce, se asume como válido para no bloquear al usuario.
            print(f"ADVERTENCIA: Tipo de validación no reconocido '{tipo_validacion}'. Se asumió como válido.")
            return True

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Valida un formato de email simple usando regex."""
        if not email or not isinstance(email, str):
            return False
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None

    @staticmethod
    def _is_valid_number(text: str) -> bool:
        """Valida si el texto es un número entero positivo."""
        return text.isdigit()

    @staticmethod
    def _is_valid_rut(rut: str) -> bool:
        """Valida un formato de RUT chileno (con o sin puntos, con guión)."""
        if not rut or not isinstance(rut, str):
            return False
        rut = rut.replace(".", "").replace("-", "").strip().lower()
        if not rut[:-1].isdigit() or not (rut[-1].isdigit() or rut[-1] == 'k'):
            return False
        # Esta es una validación de formato simple, no del dígito verificador.
        return len(rut) in [8, 9]
    
    @staticmethod
    def create(data: dict) -> RequisitoProducto:
        nuevo_req = RequisitoProducto(
            producto_id=data['producto_id'],
            nombre_requisito=data['nombre_requisito'],
            orden=data.get('orden', 0),
            opciones=data.get('opciones', [])
        )
        db.session.add(nuevo_req)
        db.session.commit()
        return nuevo_req

    @staticmethod
    def update(requisito_id: int, data: dict) -> Optional[RequisitoProducto]:
        req = RequisitoProducto.query.get(requisito_id)
        if not req:
            return None
        for key, value in data.items():
            if hasattr(req, key):
                setattr(req, key, value)
        db.session.commit()
        return req

    @staticmethod
    def delete(requisito_id: int) -> bool:
        req = RequisitoProducto.query.get(requisito_id)
        if req:
            db.session.delete(req)
            db.session.commit()
            return True
        return False