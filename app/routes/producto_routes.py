# app/routes/producto_routes.py
import requests
from app import db
from app.models import Producto, Proveedor, PreciosProducto
from sqlalchemy import distinct, func, cast, Text
from typing import List, Dict, Any, Optional

def _validate_media_url(url: str) -> bool:
    if not url: return True
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code != 200: return False
        content_type = response.headers.get('content-type', '').lower()
        if not any(allowed in content_type for allowed in ['image/', 'video/']):
            return False
        return True
    except requests.RequestException:
        return False

class ProductoRoute:
    @staticmethod
    def obtener_categorias_productos() -> List[str]:
        """Obtiene categorías de productos que están listos para la venta."""
        return [
            row[0] for row in db.session.query(distinct(Producto.categoria))
            .join(PreciosProducto, Producto.producto_id == PreciosProducto.producto_id)
            .filter(Producto.activo == True, Producto.categoria.isnot(None))
            .order_by(Producto.categoria).all()
        ]

    @staticmethod
    def obtener_productos_por_categoria(categoria: str) -> List[Dict[str, Any]]:
        """Obtiene productos formateados de una categoría específica para el chatbot."""
        productos_obj = db.session.query(Producto).join(Proveedor).join(
            PreciosProducto, Producto.producto_id == PreciosProducto.producto_id
        ).filter(
            Producto.categoria == categoria,
            Producto.activo == True,
        ).distinct(Producto.producto_id).all()
        
        productos_formateados = []
        for p in productos_obj:
            precio_min, precio_max = 0, 0
            if p.precios:
                precios_lista = [float(precio.precio_unitario) for precio in p.precios]
                if precios_lista:
                    precio_min, precio_max = min(precios_lista), max(precios_lista)

            productos_formateados.append({
                "id": p.producto_id,
                "nombre": p.nombre_producto,
                "proveedor": p.proveedor.nombre if p.proveedor else "N/A",
                "calidad_servicio": p.proveedor.calidad_servicio if p.proveedor else 0,
                "precio_min": precio_min,
                "precio_max": precio_max
            })
        return sorted(productos_formateados, key=lambda x: x['nombre'])

    @staticmethod
    def get_producto_by_id(producto_id: int) -> Optional[Producto]:
        """Obtiene un producto por su ID. Usado por el chatbot y lógica interna."""
        return Producto.query.get(producto_id)

    # --- NUEVA FUNCIÓN ESPECÍFICA PARA EL PORTAL ---
    @staticmethod
    def get_product_by_id_for_portal(producto_id: int) -> Optional[Producto]:
        """
        Busca un producto por su ID usando un método más robusto para la API,
        evitando potenciales errores de sesión con .get().
        """
        return Producto.query.filter_by(producto_id=producto_id).first()

    @staticmethod
    def get_all_for_admin() -> List[Producto]:
        return Producto.query.filter_by(activo=True).all()

    @staticmethod
    def create(data: dict) -> Producto:
        nuevo_producto = Producto(
            nombre_producto=data['nombre_producto'], sku=data.get('sku'),
            categoria=data.get('categoria'), proveedor_id=data['proveedor_id'],
            descripcion=data.get('descripcion')
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        return nuevo_producto

    @staticmethod
    def update(producto_id: int, data: dict) -> Optional[Producto]:
        producto = Producto.query.get(producto_id)
        if not producto: return None
        if 'media_url' in data and not _validate_media_url(data['media_url']):
            raise ValueError("La URL de la media no es válida o no es accesible.")
        for key, value in data.items():
            if hasattr(producto, key):
                setattr(producto, key, value)
        db.session.commit()
        return producto

    @staticmethod
    def soft_delete(producto_id: int) -> bool:
        """Realiza un borrado suave de un producto."""
        producto = Producto.query.get(producto_id)
        if producto:
            producto.activo = False
            db.session.commit()
            return True
        return False
        
    @staticmethod
    def get_product_details_for_portal(producto_id: int) -> Optional[Dict[str, Any]]:
        producto = ProductoRoute.get_product_by_id_for_portal(producto_id)
        if not producto: return None
        return {
            "producto_id": producto.producto_id, "nombre_producto": producto.nombre_producto,
            "sku": producto.sku, "descripcion": producto.descripcion,
            "requisitos": sorted([{
                "nombre_requisito": r.nombre_requisito, "opciones": r.opciones,
                "orden": r.orden
            } for r in producto.requisitos], key=lambda x: x['orden']),
            "precios": [{
                "variante": p.variante_requisitos, "cantidad_minima": p.cantidad_minima,
                "precio_unitario": float(p.precio_unitario)
            } for p in producto.precios]
        }