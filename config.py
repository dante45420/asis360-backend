# config.py

import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Carga las variables de entorno desde el archivo .env
load_dotenv()

class Config:
    """
    Clase de configuración para centralizar todas las variables de la aplicación.
    """
    # Credenciales de WhatsApp
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

    # Configuración de Base de Datos
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD_RAW = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    
    DB_PASSWORD = quote_plus(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else ""
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # NUEVO: Controla si SQLAlchemy imprime todas las consultas SQL
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() in ('true', '1', 't')

    # Datos de Pago
    BANK_NAME = os.getenv("BANK_NAME", "Banco Ficticio")
    ACCOUNT_HOLDER = os.getenv("ACCOUNT_HOLDER", "Juan Pérez")
    ACCOUNT_NUMBER = os.getenv("ACCOUNT_NUMBER", "123-456-789")
    HOLDER_RUT = os.getenv("HOLDER_RUT", "12.345.678-9")
    HOLDER_EMAIL = os.getenv("HOLDER_EMAIL", "pagos@example.com")
    
    # Clave Secreta para JWT
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("No se encontró la variable de entorno SECRET_KEY.")

    # URL del Frontend para CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL")
    
    # --- AÑADIMOS LAS VARIABLES DE AWS/S3/MINIO ---
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", None) 

    # --- VARIABLES AÑADIDAS PARA EL HILO DE TIMEOUT ---
    CONVERSATION_TIMEOUT_MINUTES = os.getenv("CONVERSATION_TIMEOUT_MINUTES", 60)
    TIMEOUT_CHECK_INTERVAL_MINUTES = os.getenv("TIMEOUT_CHECK_INTERVAL_MINUTES", 5)