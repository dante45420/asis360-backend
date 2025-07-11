# app/services/s3_service.py
import boto3
from flask import current_app
import requests

def _get_s3_client():
    """Crea y devuelve un cliente de S3 configurado."""
    return boto3.client(
        's3',
        endpoint_url=current_app.config.get('AWS_ENDPOINT_URL'),
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

def upload_file_to_s3(file_data, bucket_name, object_name):
    """Sube datos de un archivo y devuelve la ruta (key) del objeto."""
    s3_client = _get_s3_client()
    try:
        s3_client.put_object(
            Bucket=bucket_name, Key=object_name,
            Body=file_data, ContentType='image/jpeg'
        )
        print(f"Archivo subido a S3/MinIO con la ruta: {object_name}")
        return object_name # <-- AHORA DEVUELVE LA RUTA, NO LA URL
    except Exception as e:
        print(f"Error al subir archivo a S3/MinIO: {e}")
        return None

# --- NUEVA FUNCIÓN AÑADIDA ---
def upload_file_from_url(url: str, bucket: str, object_name: str):
    """Descarga un archivo desde una URL y lo sube a S3/MinIO."""
    print('provando fotos')
    try:
        headers = {'Authorization': f'Bearer {current_app.config["WHATSAPP_TOKEN"]}'}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status() # Lanza un error si la descarga falla
        
        # Usamos la función existente para subir el contenido descargado
        return upload_file_to_s3(response.content, bucket, object_name)
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo desde la URL: {e}")
        return None

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """NUEVA FUNCIÓN: Genera una URL pre-firmada para un objeto privado."""
    s3_client = _get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error al generar URL pre-firmada: {e}")
        return None