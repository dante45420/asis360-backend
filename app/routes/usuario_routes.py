# app/routes/usuario_routes.py
from app import db
from app.models import Usuario, PerfilCliente
from typing import Optional

class UsuarioRoute:
    @staticmethod
    def get_by_phone(phone_number: str) -> Optional[Usuario]:
        return Usuario.query.filter_by(telefono=phone_number).first()

    @staticmethod
    def create(nombre: str, email: str, telefono: str, password: str, rol: str = 'cliente') -> Usuario:
        """
        Crea un nuevo usuario y hashea su contraseña.
        Esta es ahora la única fuente para crear un Usuario.
        """
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email.lower(),
            telefono=telefono,
            rol=rol
        )
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        return nuevo_usuario

    @staticmethod
    def get_by_id(usuario_id: int) -> Optional[Usuario]:
        return Usuario.query.get(usuario_id)

    @staticmethod
    def find_by_email(email: str) -> Optional[Usuario]:
        """Busca un usuario por su dirección de email."""
        if not email:
            return None
        return Usuario.query.filter_by(email=email.lower()).first()

    @staticmethod
    def update(usuario_id: int, data: dict) -> Optional[Usuario]:
        """Actualiza campos de un usuario existente."""
        usuario = Usuario.query.get(usuario_id)
        if usuario:
            for key, value in data.items():
                if hasattr(usuario, key) and key != 'password_hash': # Evitar sobreescribir hash directamente
                    setattr(usuario, key, value)
            db.session.commit()
        return usuario
    
    # --- MÉTODO NUEVO AÑADIDO ---
    @staticmethod
    def create_with_profile(nombre: str, email: str, password: str, telefono: str, rol: str = 'cliente') -> Optional[Usuario]:
        """
        Crea un nuevo Usuario y su PerfilCliente asociado en una sola transacción.
        """
        try:
            # Crear la instancia del Usuario
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email.lower(),
                telefono=telefono,
                rol=rol
            )
            nuevo_usuario.set_password(password)
            db.session.add(nuevo_usuario)
            
            # Hacer un flush para obtener el usuario_id para el perfil
            db.session.flush()

            # Crear la instancia del PerfilCliente
            nuevo_perfil = PerfilCliente(
                usuario_id=nuevo_usuario.usuario_id,
                nombre=nombre,
                telefono_vinculado=telefono
            )
            db.session.add(nuevo_perfil)
            
            # Hacer commit para guardar ambos en la base de datos
            db.session.commit()
            
            print(f"Usuario y perfil creados exitosamente para {email}")
            return nuevo_usuario
            
        except Exception as e:
            # Si algo sale mal, hacer rollback para no dejar datos inconsistentes
            db.session.rollback()
            print(f"Error en la transacción de create_with_profile: {e}", exc_info=True)
            return None