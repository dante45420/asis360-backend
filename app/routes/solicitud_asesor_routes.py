# app/routes/solicitud_asesor_routes.py
from app import db
from app.models.solicitud_asesor_model import SolicitudAsesor

class SolicitudAsesorRoute:
    @staticmethod
    def create(perfil_cliente_id: int, metodo: str, detalles: str = None, asesor_id: int = None) -> SolicitudAsesor:
        nueva_solicitud = SolicitudAsesor(
            perfil_cliente_id=perfil_cliente_id,
            metodo_contacto=metodo,
            detalles_adicionales=detalles,
            asesor_asignado_id=asesor_id # Se puede asignar al crear
        )
        db.session.add(nueva_solicitud)
        db.session.commit()
        return nueva_solicitud