# manage_db.py

import click
import os
from decimal import Decimal, ROUND_DOWN
from app import create_app, db

# Asumo que tus modelos están en app/models/ y se llaman así.
# Si la estructura o los nombres son diferentes, ajústalos aquí.
from app.models import (
    Usuario, Organizacion, PerfilCliente, Proveedor, PerfilProveedor,
    Producto, RequisitoProducto, PreciosProducto, Pedido, DetallePedido,
    Conversacion, Mensaje, SoporteResolucion, TicketProducto
)

app = create_app()

# -----------------------------------------------------------------------------
# DEFINICIÓN DE COMANDOS DE LÍNEA (CLI)
# -----------------------------------------------------------------------------

@click.group()
def cli():
    """Comandos de línea para la gestión de la base de datos."""
    pass

@cli.command('create')
@click.option('--force', is_flag=True, help='Elimina las tablas existentes antes de crearlas.')
def create(force):
    """Crea todas las tablas de la base de datos."""
    with app.app_context():
        if force:
            print("Eliminando todas las tablas existentes...")
            db.drop_all()
        print("Creando todas las tablas...")
        db.create_all()
        print("Tablas creadas exitosamente.")

@cli.command('drop')
def drop():
    """Elimina todas las tablas de la base de datos."""
    with app.app_context():
        if click.confirm('¿Estás seguro de que quieres eliminar todas las tablas? Esta acción es irreversible.'):
            print("Eliminando todas las tablas...")
            db.drop_all()
            print("Tablas eliminadas exitosamente.")
        else:
            print("Operación cancelada.")

# -----------------------------------------------------------------------------
# COMANDO PRINCIPAL PARA POBLAR LA BASE DE DATOS (SEED)
# -----------------------------------------------------------------------------

@cli.command('seed')
def seed():
    """
    Puebla la base de datos con un ecosistema de producción completo.
    """
    with app.app_context():
        print("=====================================================")
        print("= INICIANDO PROCESO DE SEEDING COMPLETO =")
        print("=====================================================")

        # --- 1. Limpieza de la base de datos ---
        print("\n[Paso 1/5] Limpiando la base de datos...")
        DetallePedido.query.delete()
        PreciosProducto.query.delete()
        RequisitoProducto.query.delete()
        Producto.query.delete()
        Proveedor.query.delete()
        # Puedes añadir más tablas si es necesario
        db.session.commit()
        # Limpiamos usuarios al final
        Usuario.query.delete()
        db.session.commit()
        print("-> Base de datos limpia.")

        # --- 2. Creación de Admin Profesional y Seguro ---
        print("\n[Paso 2/5] Creando usuario administrador...")
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not all([admin_email, admin_password]):
            print("\n!!! ERROR: Faltan las variables de entorno ADMIN_EMAIL o ADMIN_PASSWORD.")
            print("!!! No se puede crear el administrador. Cancela la operación.")
            return

        if Usuario.query.filter_by(email=admin_email).first():
            print(f"-> El usuario administrador con email '{admin_email}' ya existe.")
        else:
            admin_user = Usuario(
                nombre=os.getenv("ADMIN_NAME", "Admin Principal"),
                telefono=os.getenv("ADMIN_PHONE", "+56900000000"),
                email=admin_email,
                rol='admin'
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"-> Usuario administrador '{admin_email}' creado exitosamente.")

        # --- 3. Definición de Funciones de Ayuda (Helpers) ---
        print("\n[Paso 3/5] Definiendo funciones de ayuda...")
        
        def generate_price_breaks(base_price_str):
            """Calcula precios con descuento para 10, 50, 100, 200, 500 y 10000 unidades."""
            base_price = Decimal(base_price_str)
            discounts = {
                10: Decimal('0.95'),    # 5% de descuento
                50: Decimal('0.92'),    # 8% de descuento
                100: Decimal('0.88'),   # 12% de descuento
                200: Decimal('0.85'),   # 15% de descuento
                500: Decimal('0.82'),   # 18% de descuento
                10000: Decimal('0.75')  # 25% de descuento
            }
            price_breaks = [{'cantidad_minima': 1, 'precio_unitario': base_price}]
            for qty, multiplier in discounts.items():
                discounted_price = (base_price * multiplier).quantize(Decimal('0'), rounding=ROUND_DOWN)
                price_breaks.append({'cantidad_minima': qty, 'precio_unitario': discounted_price})
            return price_breaks

        def add_mandatory_reqs(product_id):
            """Añade los requisitos de Cantidad, RUT y Dirección a un producto."""
            reqs = [
                RequisitoProducto(
                    producto_id=product_id,
                    nombre_requisito="Cantidad",
                    orden=97,  # Un número alto para que se pregunte al final
                    tipo_dato="Numero",
                    tipo_validacion="numero_entero_positivo"
                ),
                RequisitoProducto(
                    producto_id=product_id,
                    nombre_requisito="RUT para Factura",
                    orden=98,
                    tipo_dato="Texto",
                    tipo_validacion="texto_simple" # En el futuro, podrías crear una validación específica para RUT.
                ),
                RequisitoProducto(
                    producto_id=product_id,
                    nombre_requisito="Dirección de Despacho",
                    orden=99,
                    tipo_dato="Texto",
                    tipo_validacion="texto_simple"
                )
            ]
            db.session.add_all(reqs)
        
        print("-> Funciones de ayuda listas.")

        # --- 4. Creación de Proveedores ---
        print("\n[Paso 4/5] Creando el ecosistema de proveedores...")
        
        # DEFINIMOS 8 CATEGORÍAS CLARAS
        # 1. Café e Infusiones
        # 2. Lácteos y Bebidas
        # 3. Panadería y Pastelería
        # 4. Abarrotes y Conservas
        # 5. Frutas y Verduras
        # 6. Desechables y Packaging
        # 7. Limpieza e Higiene
        # 8. Congelados y Preparados

        providers_data = [
            # Proveedores para Café, Pastelería y Abarrotes
            {"nombre": "Café del Sur", "info_contacto": "ventas@cafedelsur.cl", "calidad_servicio": 9},
            {"nombre": "Tostaduría Andina", "info_contacto": "contacto@tostaduriaandina.cl", "calidad_servicio": 8},
            {"nombre": "Delicias de la Abuela", "info_contacto": "pedidos@deliciasabuela.cl", "calidad_servicio": 9},
            {"nombre": "Panadería La Tradición", "info_contacto": "contacto@latradicion.cl", "calidad_servicio": 8},
            {"nombre": "Comercial Surtido", "info_contacto": "ventas@surtido.cl", "calidad_servicio": 8},
            {"nombre": "Iansafood", "info_contacto": "contacto.foodservice@iansa.cl", "calidad_servicio": 9},
            
            # Proveedores para Lácteos y Bebidas
            {"nombre": "Lácteos del Valle", "info_contacto": "pedidos@lacteosdelvalle.cl", "calidad_servicio": 8},
            {"nombre": "Surlat", "info_contacto": "contacto@surlat.cl", "calidad_servicio": 9},
            {"nombre": "Distribuidora Andina", "info_contacto": "hablemos@koandina.com", "calidad_servicio": 9},
            {"nombre": "CCU", "info_contacto": "servicio.cliente@ccu.cl", "calidad_servicio": 9},

            # Proveedores para Frutas y Verduras
            {"nombre": "Frutas Frescas Lo Valledor", "info_contacto": "despachos@frutasfrescas.cl", "calidad_servicio": 8},
            {"nombre": "CampoDirecto SpA", "info_contacto": "hola@campodirecto.cl", "calidad_servicio": 9},
            
            # Proveedores para Desechables y Limpieza
            {"nombre": "Ecologico-Pack", "info_contacto": "ventas@ecopack.cl", "calidad_servicio": 8},
            {"nombre": "BioPack Chile", "info_contacto": "info@biopack.cl", "calidad_servicio": 9},
            {"nombre": "Limpieza Total Pro", "info_contacto": "contacto@limpiezatotal.pro", "calidad_servicio": 8},
            {"nombre": "Virutex", "info_contacto": "ventas@virutex.cl", "calidad_servicio": 9},

            # Proveedores para Congelados
            {"nombre": "BredenMaster", "info_contacto": "ventas.horeca@bredenmaster.com", "calidad_servicio": 8},
            {"nombre": "Frutos del Maipo", "info_contacto": "contacto@frutosdelmaipo.cl", "calidad_servicio": 9},
        ]
        
        providers = {}
        for data in providers_data:
            prov = Proveedor(**data)
            db.session.add(prov)
            providers[data['nombre']] = prov
        db.session.commit()
        print(f"-> {len(providers_data)} proveedores creados exitosamente.")

        # --- 5. Creación de Productos, Requisitos y Precios ---
        print("\n[Paso 5/5] Poblando el catálogo de productos...")
        
        # =====================================================================
        # CATEGORÍA 1: CAFÉ E INFUSIONES
        # =====================================================================
        
        # --- PRODUCTOS PARA "Café del Sur" ---
        prov_id = providers["Café del Sur"].proveedor_id
        
        # Producto 1: Café de Especialidad en Grano
        p = Producto(proveedor_id=prov_id, nombre_producto="Café de Especialidad en Grano", categoria="Café e Infusiones", descripcion="Grano 100% arábica de tueste artesanal. Notas a chocolate y frutos secos. Perfecto para espresso o filtrado.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 250g']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tostado", orden=2, opciones=['Medio', 'Oscuro'])])
        db.session.commit()
        for price_point in generate_price_breaks("18990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Tostado': 'Medio'}, **price_point))
        for price_point in generate_price_breaks("19500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Tostado': 'Oscuro'}, **price_point))
        for price_point in generate_price_breaks("6990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 250g', 'Tostado': 'Medio'}, **price_point))
        for price_point in generate_price_breaks("7200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 250g', 'Tostado': 'Oscuro'}, **price_point))

        # Producto 2: Café Molido Tradicional
        p = Producto(proveedor_id=prov_id, nombre_producto="Café Molido Tradicional", categoria="Café e Infusiones", descripcion="Mezcla de granos arábica y robusta para un sabor intenso y equilibrado. Ideal para cafetera italiana o de goteo.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 500g']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Molienda", orden=2, opciones=['Fina (Espresso)', 'Media (Goteo)'])])
        db.session.commit()
        for price_point in generate_price_breaks("14500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Media (Goteo)'}, **price_point))
        for price_point in generate_price_breaks("8500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g', 'Molienda': 'Media (Goteo)'}, **price_point))
        for price_point in generate_price_breaks("8900"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g', 'Molienda': 'Fina (Espresso)'}, **price_point))

        # Producto 3: Cápsulas de Café Compatibles
        p = Producto(proveedor_id=prov_id, nombre_producto="Cápsulas de Café Compatibles Nespresso", categoria="Café e Infusiones", descripcion="Disfruta de nuestro mejor café en la comodidad de una cápsula. Intensidad y aroma garantizados.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 50 unidades', 'Caja 100 unidades']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Intensidad", orden=2, opciones=['Suave (6)', 'Medio (8)', 'Intenso (10)'])])
        db.session.commit()
        for price_point in generate_price_breaks("19990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 50 unidades', 'Intensidad': 'Medio (8)'}, **price_point))
        for price_point in generate_price_breaks("21990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 50 unidades', 'Intensidad': 'Intenso (10)'}, **price_point))
        for price_point in generate_price_breaks("37990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 100 unidades', 'Intensidad': 'Medio (8)'}, **price_point))

        # Producto 4: Té Negro Ceylan en Bolsitas
        p = Producto(proveedor_id=prov_id, nombre_producto="Té Negro Ceylan Premium", categoria="Café e Infusiones", descripcion="Té negro de hoja larga de Sri Lanka. Sabor robusto y color profundo, perfecto para empezar el día.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 20 bolsitas', 'Caja 100 bolsitas']))
        db.session.commit()
        for price_point in generate_price_breaks("3500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 20 bolsitas'}, **price_point))
        for price_point in generate_price_breaks("14990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 100 bolsitas'}, **price_point))
        
        # Producto 5: Infusión de Manzanilla y Miel
        p = Producto(proveedor_id=prov_id, nombre_producto="Infusión de Manzanilla y Miel", categoria="Café e Infusiones", descripcion="Relajante infusión de flores de manzanilla con un toque dulce de miel natural. Sin cafeína.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 20 bolsitas', 'Caja 100 bolsitas']))
        db.session.commit()
        for price_point in generate_price_breaks("3800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 20 bolsitas'}, **price_point))
        for price_point in generate_price_breaks("16500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 100 bolsitas'}, **price_point))

        # Producto 6: Syrup Saborizante para Café
        p = Producto(proveedor_id=prov_id, nombre_producto="Syrup Saborizante para Café", categoria="Café e Infusiones", descripcion="Añade un toque gourmet a tus bebidas. Perfecto para lattes, capuccinos y frappés. Botella de vidrio de 1L.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Sabor", orden=1, opciones=['Vainilla', 'Caramelo', 'Avellana', 'Chocolate Blanco']))
        db.session.commit()
        for price_point in generate_price_breaks("8990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Vainilla'}, **price_point))
        for price_point in generate_price_breaks("8990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Caramelo'}, **price_point))
        for price_point in generate_price_breaks("9500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Avellana'}, **price_point))
        for price_point in generate_price_breaks("9800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Chocolate Blanco'}, **price_point))
        
        # Producto 7: Chocolate en Polvo para Moka
        p = Producto(proveedor_id=prov_id, nombre_producto="Chocolate en Polvo para Moka 33% Cacao", categoria="Café e Infusiones", descripcion="Polvo de cacao de alta calidad, semi-dulce, se disuelve fácilmente. Ideal para mokaccinos y chocolate caliente.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Tarro 3kg']))
        db.session.commit()
        for price_point in generate_price_breaks("11500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("31000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Tarro 3kg'}, **price_point))

        # Producto 8: Café Descafeinado en Grano
        p = Producto(proveedor_id=prov_id, nombre_producto="Café Descafeinado en Grano", categoria="Café e Infusiones", descripcion="Todo el sabor de un buen café, sin cafeína. Proceso de descafeinado natural al agua. Tueste medio.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 500g']))
        db.session.commit()
        for price_point in generate_price_breaks("21000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("11500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g'}, **price_point))

        # Producto 9: Leche Condensada para Café Bombón
        p = Producto(proveedor_id=prov_id, nombre_producto="Leche Condensada", categoria="Café e Infusiones", descripcion="Leche condensada cremosa y dulce, el ingrediente secreto para un café bombón perfecto y otras preparaciones.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Tarro 397g', 'Botella 1kg']))
        db.session.commit()
        for price_point in generate_price_breaks("2500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Tarro 397g'}, **price_point))
        for price_point in generate_price_breaks("5500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 1kg'}, **price_point))
        
        # Producto 10: Café Instantáneo Liofilizado
        p = Producto(proveedor_id=prov_id, nombre_producto="Café Instantáneo Liofilizado", categoria="Café e Infusiones", descripcion="Café premium instantáneo, proceso liofilizado que conserva el máximo aroma y sabor. Rápido y delicioso.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Frasco 170g', 'Bolsa Doypack 500g']))
        db.session.commit()
        for price_point in generate_price_breaks("8900"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Frasco 170g'}, **price_point))
        for price_point in generate_price_breaks("23500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa Doypack 500g'}, **price_point))
        
        db.session.commit()
        print("-> Productos para 'Café del Sur' cargados.")

        # --- PRODUCTOS PARA "Tostaduría Andina" ---
        prov_id = providers["Tostaduría Andina"].proveedor_id
        
        # Producto 1: Café de Origen Colombia
        p = Producto(proveedor_id=prov_id, nombre_producto="Café de Origen Único: Colombia", categoria="Café e Infusiones", descripcion="Grano de Caturra de la región de Huila. Notas cítricas y dulces con acidez brillante. Tueste medio claro.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 500g']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Molienda", orden=2, opciones=['Grano Entero', 'Media (V60)', 'Fina (Aeropress)'])])
        db.session.commit()
        for price_point in generate_price_breaks("24000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Grano Entero'}, **price_point))
        for price_point in generate_price_breaks("13000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g', 'Molienda': 'Grano Entero'}, **price_point))
        for price_point in generate_price_breaks("13500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g', 'Molienda': 'Media (V60)'}, **price_point))

        # Producto 2: Café de Origen Etiopía
        p = Producto(proveedor_id=prov_id, nombre_producto="Café de Origen Único: Etiopía", categoria="Café e Infusiones", descripcion="Grano Heirloom de Yirgacheffe. Proceso lavado. Perfil floral y notas a té de bergamota y limón.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 250g']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Molienda", orden=2, opciones=['Grano Entero', 'Gruesa (Prensa Francesa)'])])
        db.session.commit()
        for price_point in generate_price_breaks("28000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Grano Entero'}, **price_point))
        for price_point in generate_price_breaks("8500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 250g', 'Molienda': 'Grano Entero'}, **price_point))

        # Producto 3: Blend de la Casa Espresso
        p = Producto(proveedor_id=prov_id, nombre_producto="Blend de la Casa 'Andino'", categoria="Café e Infusiones", descripcion="Mezcla especial de granos de Brasil y Perú, diseñada para un espresso balanceado, con cuerpo y crema persistente.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Molienda", orden=2, opciones=['Grano Entero', 'Fina (Espresso)'])])
        db.session.commit()
        for price_point in generate_price_breaks("21000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Grano Entero'}, **price_point))
        for price_point in generate_price_breaks("21500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Fina (Espresso)'}, **price_point))
        
        # Producto 4: Té Matcha Grado Ceremonial
        p = Producto(proveedor_id=prov_id, nombre_producto="Té Matcha Grado Ceremonial", categoria="Café e Infusiones", descripcion="Polvo fino de té verde de Japón. Color verde vibrante y sabor suave, sin amargor. Ideal para lattes o beber solo.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Lata 30g', 'Bolsa 100g'])])
        db.session.commit()
        for price_point in generate_price_breaks("15000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Lata 30g'}, **price_point))
        for price_point in generate_price_breaks("42000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 100g'}, **price_point))
        
        # Producto 5: Rooibos Vainilla en Hojas
        p = Producto(proveedor_id=prov_id, nombre_producto="Rooibos Vainilla en Hojas", categoria="Café e Infusiones", descripcion="Infusión sudafricana naturalmente sin cafeína, con trozos de vaina de vainilla. Dulce y reconfortante.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 100g', 'Bolsa 250g'])])
        db.session.commit()
        for price_point in generate_price_breaks("7500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 100g'}, **price_point))
        for price_point in generate_price_breaks("16000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 250g'}, **price_point))
        
        # Producto 6: Cold Brew Concentrate
        p = Producto(proveedor_id=prov_id, nombre_producto="Concentrado de Cold Brew", categoria="Café e Infusiones", descripcion="Café extraído en frío por 18 horas. Suave, bajo en acidez y muy versátil. Solo añade agua o leche.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Botella 1L', 'Bag-in-Box 5L'])])
        db.session.commit()
        for price_point in generate_price_breaks("12000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 1L'}, **price_point))
        for price_point in generate_price_breaks("55000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bag-in-Box 5L'}, **price_point))
        
        # Producto 7: Café en grano Geisha de Panamá
        p = Producto(proveedor_id=prov_id, nombre_producto="Café Exclusivo: Geisha de Panamá", categoria="Café e Infusiones", descripcion="Lote exclusivo de la aclamada variedad Geisha. Perfil de sabor complejo con notas a jazmín, papaya y mandarina.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 150g'])])
        db.session.commit()
        for price_point in generate_price_breaks("35000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 150g'}, **price_point))
        
        # Producto 8: Cascara de Café (Té de Café)
        p = Producto(proveedor_id=prov_id, nombre_producto="Infusión de Cáscara de Café", categoria="Café e Infusiones", descripcion="Pulpa deshidratada del fruto del café. Una infusión única con notas a frutos rojos, hibisco y un toque dulce.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 100g', 'Bolsa 250g'])])
        db.session.commit()
        for price_point in generate_price_breaks("6500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 100g'}, **price_point))
        for price_point in generate_price_breaks("14000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 250g'}, **price_point))
        
        # Producto 9: Café de Origen Perú
        p = Producto(proveedor_id=prov_id, nombre_producto="Café de Origen Único: Perú", categoria="Café e Infusiones", descripcion="Grano de Cajamarca, cultivado en altura. Perfil de sabor suave con notas a caramelo, nuez y un final limpio.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Bolsa 500g']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Molienda", orden=2, opciones=['Grano Entero', 'Media (Goteo)'])])
        db.session.commit()
        for price_point in generate_price_breaks("22500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg', 'Molienda': 'Grano Entero'}, **price_point))
        for price_point in generate_price_breaks("12000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 500g', 'Molienda': 'Media (Goteo)'}, **price_point))

        # Producto 10: Filtros de Papel V60
        p = Producto(proveedor_id=prov_id, nombre_producto="Filtros de Papel para V60", categoria="Café e Infusiones", descripcion="Filtros de papel blanco, cónicos, diseñados para el método de goteo V60. No alteran el sabor del café.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tamaño", orden=1, opciones=['01 (1-2 tazas)', '02 (1-4 tazas)']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=2, opciones=['Paquete 100 unidades'])])
        db.session.commit()
        for price_point in generate_price_breaks("6000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '01 (1-2 tazas)', 'Formato': 'Paquete 100 unidades'}, **price_point))
        for price_point in generate_price_breaks("7000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '02 (1-4 tazas)', 'Formato': 'Paquete 100 unidades'}, **price_point))

        db.session.commit()
        print("-> Productos para 'Tostaduría Andina' cargados.")

        # =====================================================================
        # CATEGORÍA 2: LÁCTEOS Y BEBIDAS
        # =====================================================================

        # --- PRODUCTOS PARA "Lácteos del Valle" ---
        prov_id = providers["Lácteos del Valle"].proveedor_id
        
        # Producto 1: Leche Entera UHT
        p = Producto(proveedor_id=prov_id, nombre_producto="Leche Entera UHT Larga Vida", categoria="Lácteos y Bebidas", descripcion="Leche 100% de vaca, procesada para larga duración sin refrigeración. Ideal por su cremosidad para café y batidos.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 1L', 'Caja 200ml'])])
        db.session.commit()
        for price_point in generate_price_breaks("1250"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 1L'}, **price_point))
        for price_point in generate_price_breaks("650"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 200ml'}, **price_point))
        
        # Producto 2: Leche Descremada UHT
        p = Producto(proveedor_id=prov_id, nombre_producto="Leche Descremada UHT Larga Vida", categoria="Lácteos y Bebidas", descripcion="Leche ligera, 0% materia grasa, con todas las proteínas y calcio. Perfecta para opciones saludables.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 1L'])])
        db.session.commit()
        for price_point in generate_price_breaks("1290"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 1L'}, **price_point))
        
        # Producto 3: Leche Sin Lactosa UHT
        p = Producto(proveedor_id=prov_id, nombre_producto="Leche Sin Lactosa UHT Larga Vida", categoria="Lácteos y Bebidas", descripcion="Leche de fácil digestión, ideal para clientes con intolerancia a la lactosa, sin sacrificar el sabor.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tipo", orden=1, opciones=['Entera', 'Semi-descremada'])])
        db.session.commit()
        for price_point in generate_price_breaks("1450"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tipo': 'Entera'}, **price_point))
        for price_point in generate_price_breaks("1480"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tipo': 'Semi-descremada'}, **price_point))
        
        # Producto 4: Crema de Leche para Batir
        p = Producto(proveedor_id=prov_id, nombre_producto="Crema de Leche para Batir UHT", categoria="Lácteos y Bebidas", descripcion="Crema con 35% de materia grasa, ideal para montar, crear mousses y dar un toque final a postres y cafés.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 1L', 'Caja 200ml'])])
        db.session.commit()
        for price_point in generate_price_breaks("4500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 1L'}, **price_point))
        for price_point in generate_price_breaks("1500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 200ml'}, **price_point))
        
        # Producto 5: Yogurt Natural Sin Azúcar
        p = Producto(proveedor_id=prov_id, nombre_producto="Yogurt Natural Sin Azúcar", categoria="Lácteos y Bebidas", descripcion="Yogurt cremoso y ácido, elaborado solo con leche y cultivos lácticos. Base perfecta para bowls y smoothies.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Pote 1kg', 'Pote 150g'])])
        db.session.commit()
        for price_point in generate_price_breaks("3800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Pote 1kg'}, **price_point))
        for price_point in generate_price_breaks("850"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Pote 150g'}, **price_point))
        
        # Producto 6: Mantequilla con Sal
        p = Producto(proveedor_id=prov_id, nombre_producto="Mantequilla Sureña con Sal", categoria="Lácteos y Bebidas", descripcion="Mantequilla de sabor intenso y textura suave, elaborada con crema fresca de leche. Ideal para tostadas y repostería.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Barra 250g', 'Barra 125g'])])
        db.session.commit()
        for price_point in generate_price_breaks("3200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Barra 250g'}, **price_point))
        for price_point in generate_price_breaks("1800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Barra 125g'}, **price_point))
        
        # Producto 7: Bebida de Almendras
        p = Producto(proveedor_id=prov_id, nombre_producto="Bebida de Almendras Original", categoria="Lácteos y Bebidas", descripcion="Alternativa vegetal a la leche, ligera y con un suave sabor a almendras tostadas. Fortificada con vitaminas.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Endulzado", orden=1, opciones=['Con Azúcar', 'Sin Azúcar'])])
        db.session.commit()
        for price_point in generate_price_breaks("2500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Endulzado': 'Con Azúcar'}, **price_point))
        for price_point in generate_price_breaks("2650"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Endulzado': 'Sin Azúcar'}, **price_point))
        
        # Producto 8: Manjar Tradicional
        p = Producto(proveedor_id=prov_id, nombre_producto="Manjar Tradicional Estilo Campo", categoria="Lácteos y Bebidas", descripcion="Dulce de leche espeso y de color oscuro, de cocción lenta. Ideal para rellenar, decorar o acompañar postres.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Pote 1kg', 'Bolsa Pastelera 1kg'])])
        db.session.commit()
        for price_point in generate_price_breaks("6500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Pote 1kg'}, **price_point))
        for price_point in generate_price_breaks("6800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa Pastelera 1kg'}, **price_point))
        
        # Producto 9: Leche Chocolatada
        p = Producto(proveedor_id=prov_id, nombre_producto="Leche Chocolatada Lista para Servir", categoria="Lácteos y Bebidas", descripcion="La combinación perfecta de leche fresca y cacao, lista para disfrutar fría o caliente. Un clásico favorito.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 1L', 'Caja 200ml'])])
        db.session.commit()
        for price_point in generate_price_breaks("1600"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 1L'}, **price_point))
        for price_point in generate_price_breaks("750"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 200ml'}, **price_point))
        
        # Producto 10: Quesillo Fresco
        p = Producto(proveedor_id=prov_id, nombre_producto="Quesillo Fresco del Día", categoria="Lácteos y Bebidas", descripcion="Queso fresco, bajo en grasa y sal. De textura suave y sabor lácteo, perfecto para ensaladas y sándwiches.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Pieza 400g'])])
        db.session.commit()
        for price_point in generate_price_breaks("4200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Pieza 400g'}, **price_point))
        
        db.session.commit()
        print("-> Productos para 'Lácteos del Valle' cargados.")
        
        # --- PRODUCTOS PARA "Distribuidora Andina" ---
        prov_id = providers["Distribuidora Andina"].proveedor_id

        # Producto 1: Bebida Coca-Cola
        p = Producto(proveedor_id=prov_id, nombre_producto="Bebida Gaseosa Coca-Cola", categoria="Lácteos y Bebidas", descripcion="El clásico e inconfundible sabor de Coca-Cola, la bebida más famosa del mundo. Perfecta para cualquier ocasión.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Sabor", orden=1, opciones=['Original', 'Sin Azúcar', 'Light']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=2, opciones=['Lata 350cc', 'Botella 591cc', 'Botella Vidrio 237cc'])])
        db.session.commit()
        for price_point in generate_price_breaks("850"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Original', 'Formato': 'Lata 350cc'}, **price_point))
        for price_point in generate_price_breaks("900"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Sin Azúcar', 'Formato': 'Lata 350cc'}, **price_point))
        for price_point in generate_price_breaks("1200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Original', 'Formato': 'Botella 591cc'}, **price_point))
        for price_point in generate_price_breaks("700"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Original', 'Formato': 'Botella Vidrio 237cc'}, **price_point))

        # Producto 2: Agua Mineral Benedictino
        p = Producto(proveedor_id=prov_id, nombre_producto="Agua Mineral Benedictino", categoria="Lácteos y Bebidas", descripcion="Agua mineral de vertiente, pura y natural. Una opción refrescante y saludable para tus clientes.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Gas", orden=1, opciones=['Con Gas', 'Sin Gas']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=2, opciones=['Botella 500ml', 'Botella 1.5L'])])
        db.session.commit()
        for price_point in generate_price_breaks("750"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Gas': 'Sin Gas', 'Formato': 'Botella 500ml'}, **price_point))
        for price_point in generate_price_breaks("800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Gas': 'Con Gas', 'Formato': 'Botella 500ml'}, **price_point))
        for price_point in generate_price_breaks("1300"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Gas': 'Sin Gas', 'Formato': 'Botella 1.5L'}, **price_point))
        
        # ... (Resto de productos para Distribuidora Andina y otros proveedores de la categoría) ...

        db.session.commit()
        print("-> Productos para 'Distribuidora Andina' cargados.")

        # =====================================================================
        # CATEGORÍA 3: PANADERÍA Y PASTELERÍA
        # =====================================================================

        # --- PRODUCTOS PARA "Delicias de la Abuela" ---
        prov_id = providers["Delicias de la Abuela"].proveedor_id

        # Producto 1: Torta de Milhojas
        p = Producto(proveedor_id=prov_id, nombre_producto="Torta de Milhojas Manjar", categoria="Panadería y Pastelería", descripcion="Clásica torta de finas hojas de masa crujiente, rellena con abundante manjar casero y un toque de crema.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tamaño", orden=1, opciones=['15 personas', '25 personas'])])
        db.session.commit()
        for price_point in generate_price_breaks("25000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '15 personas'}, **price_point))
        for price_point in generate_price_breaks("38000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '25 personas'}, **price_point))

        # Producto 2: Pie de Limón
        p = Producto(proveedor_id=prov_id, nombre_producto="Pie de Limón con Merengue", categoria="Panadería y Pastelería", descripcion="Base de galleta, relleno cremoso y ácido de limón, coronado con un merengue italiano perfectamente dorado.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tamaño", orden=1, opciones=['Individual', 'Entero (8 porciones)'])])
        db.session.commit()
        for price_point in generate_price_breaks("3500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': 'Individual'}, **price_point))
        for price_point in generate_price_breaks("22000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': 'Entero (8 porciones)'}, **price_point))

        # ... (Resto de productos para Delicias de la Abuela y otros proveedores de la categoría) ...
        
        db.session.commit()
        print("-> Productos para 'Delicias de la Abuela' cargados.")

        # =====================================================================
        # CATEGORÍA 4: ABARROTES Y CONSERVAS
        # =====================================================================

        # --- PRODUCTOS PARA "Comercial Surtido" ---
        prov_id = providers["Comercial Surtido"].proveedor_id
        
        # Producto 1: Aceite de Maravilla
        p = Producto(proveedor_id=prov_id, nombre_producto="Aceite de Maravilla", categoria="Abarrotes y Conservas", descripcion="Aceite vegetal puro de maravilla, ligero y versátil para todo tipo de cocción, frituras y aderezos.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Botella 1L', 'Bidón 5L']))
        db.session.commit()
        for price_point in generate_price_breaks("2800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 1L'}, **price_point))
        for price_point in generate_price_breaks("12500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bidón 5L'}, **price_point))

        # Producto 2: Arroz Grado 1
        p = Producto(proveedor_id=prov_id, nombre_producto="Arroz Blanco Grado 1", categoria="Abarrotes y Conservas", descripcion="Arroz de grano largo, seleccionado por su calidad y rendimiento. El acompañamiento perfecto para cualquier plato.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Saco 5kg']))
        db.session.commit()
        for price_point in generate_price_breaks("1900"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("8900"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Saco 5kg'}, **price_point))

        # Producto 3: Atún Lomitos en Aceite
        p = Producto(proveedor_id=prov_id, nombre_producto="Atún Lomitos en Conserva", categoria="Abarrotes y Conservas", descripcion="Lomitos de atún de alta calidad, conservados para mantener su sabor y textura. Ideal para sándwiches y ensaladas.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Conserva", orden=1, opciones=['En Aceite', 'En Agua']))
        db.session.commit()
        for price_point in generate_price_breaks("1800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Conserva': 'En Aceite'}, **price_point))
        for price_point in generate_price_breaks("1750"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Conserva': 'En Agua'}, **price_point))

        # Producto 4: Duraznos en Cubitos
        p = Producto(proveedor_id=prov_id, nombre_producto="Duraznos en Cubitos en Almíbar", categoria="Abarrotes y Conservas", descripcion="Trozos de durazno jugosos y dulces, en un almíbar ligero. Listos para usar en postres, tortas o con crema.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Lata 820g', 'Lata 425g']))
        db.session.commit()
        for price_point in generate_price_breaks("2600"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Lata 820g'}, **price_point))
        for price_point in generate_price_breaks("1500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Lata 425g'}, **price_point))

        # Producto 5: Harina de Trigo sin Polvos
        p = Producto(proveedor_id=prov_id, nombre_producto="Harina de Trigo 0000", categoria="Abarrotes y Conservas", descripcion="Harina de trigo extrafina y sin polvos de hornear, ideal para panadería y pastelería profesional que requiere control total.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Saco 25kg']))
        db.session.commit()
        for price_point in generate_price_breaks("1600"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("29990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Saco 25kg'}, **price_point))
        
        db.session.commit()
        print("-> Productos para 'Comercial Surtido' cargados.")

        # --- PRODUCTOS PARA "Iansafood" ---
        prov_id = providers["Iansafood"].proveedor_id

        # Producto 1: Azúcar Granulada
        p = Producto(proveedor_id=prov_id, nombre_producto="Azúcar Blanca Granulada Iansa", categoria="Abarrotes y Conservas", descripcion="Azúcar de remolacha de alta pureza y disolución perfecta. El endulzante clásico para todas tus preparaciones.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Saco 25kg']))
        db.session.commit()
        for price_point in generate_price_breaks("1850"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("32000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Saco 25kg'}, **price_point))

        # Producto 2: Endulzante Cero K
        p = Producto(proveedor_id=prov_id, nombre_producto="Endulzante Líquido Cero K", categoria="Abarrotes y Conservas", descripcion="Endulzante sin calorías a base de sucralosa y estevia, ideal para dar dulzor a bebidas frías y calientes.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Botella 270ml', 'Botella 500ml']))
        db.session.commit()
        for price_point in generate_price_breaks("4200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 270ml'}, **price_point))
        for price_point in generate_price_breaks("7500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 500ml'}, **price_point))

        # Producto 3: Ketchup Iansa
        p = Producto(proveedor_id=prov_id, nombre_producto="Ketchup de Tomate Iansa", categoria="Abarrotes y Conservas", descripcion="Salsa de tomate ketchup de sabor clásico, elaborada con tomates seleccionados. El aderezo perfecto para sándwiches y picoteos.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Doypack 1kg', 'Botella 500g']))
        db.session.commit()
        for price_point in generate_price_breaks("4500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Doypack 1kg'}, **price_point))
        for price_point in generate_price_breaks("2600"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 500g'}, **price_point))

        # ... (Resto de productos para Iansafood) ...
        
        db.session.commit()
        print("-> Productos para 'Iansafood' cargados.")

        # =====================================================================
        # CATEGORÍA 5: FRUTAS Y VERDURAS
        # =====================================================================

        # --- PRODUCTOS PARA "Frutas Frescas Lo Valledor" ---
        prov_id = providers["Frutas Frescas Lo Valledor"].proveedor_id
        
        # Producto 1: Palta Hass
        p = Producto(proveedor_id=prov_id, nombre_producto="Palta Hass de Calidad", categoria="Frutas y Verduras", descripcion="Palta Hass cremosa y de excelente calibre. Perfecta para tostadas, sándwiches y preparaciones gourmet.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Calidad", orden=1, opciones=['Primera', 'Segunda']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=2, opciones=['Por Kilo'])])
        db.session.commit()
        for price_point in generate_price_breaks("6500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Calidad': 'Primera', 'Formato': 'Por Kilo'}, **price_point))
        for price_point in generate_price_breaks("5200"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Calidad': 'Segunda', 'Formato': 'Por Kilo'}, **price_point))

        # Producto 2: Limón para Jugo
        p = Producto(proveedor_id=prov_id, nombre_producto="Limón para Jugo (Sutil)", categoria="Frutas y Verduras", descripcion="Limón jugoso y de piel delgada, ideal para exprimir y usar en bebidas, aderezos y repostería.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Malla 1kg', 'Saco 5kg'])])
        db.session.commit()
        for price_point in generate_price_breaks("1800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Malla 1kg'}, **price_point))
        for price_point in generate_price_breaks("8500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Saco 5kg'}, **price_point))

        # Producto 3: Tomate Larga Vida
        p = Producto(proveedor_id=prov_id, nombre_producto="Tomate Larga Vida", categoria="Frutas y Verduras", descripcion="Tomate de pulpa firme y mayor duración, perfecto para sándwiches y ensaladas que requieren una buena presentación.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Por Kilo'])])
        db.session.commit()
        for price_point in generate_price_breaks("1990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Por Kilo'}, **price_point))

        # ... (Resto de productos para Frutas Frescas Lo Valledor) ...

        db.session.commit()
        print("-> Productos para 'Frutas Frescas Lo Valledor' cargados.")

        # =====================================================================
        # CATEGORÍA 6: DESECHABLES Y PACKAGING
        # =====================================================================

        # --- PRODUCTOS PARA "Ecologico-Pack" ---
        prov_id = providers["Ecologico-Pack"].proveedor_id
        
        # Producto 1: Vaso de Cartón para Café
        p = Producto(proveedor_id=prov_id, nombre_producto="Vaso de Cartón para Bebida Caliente", categoria="Desechables y Packaging", descripcion="Vaso de cartón de pared simple con recubrimiento interior de PLA. Perfecto para café, té y otras bebidas calientes.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tamaño", orden=1, opciones=['8oz (240cc)', '12oz (360cc)']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Diseño", orden=2, opciones=['Blanco', 'Kraft'])])
        db.session.commit()
        for price_point in generate_price_breaks("95"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '8oz (240cc)', 'Diseño': 'Kraft'}, **price_point))
        for price_point in generate_price_breaks("120"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '12oz (360cc)', 'Diseño': 'Kraft'}, **price_point))
        for price_point in generate_price_breaks("90"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño': '8oz (240cc)', 'Diseño': 'Blanco'}, **price_point))

        # Producto 2: Tapa Viajera para Vaso
        p = Producto(proveedor_id=prov_id, nombre_producto="Tapa Viajera para Vaso de Cartón", categoria="Desechables y Packaging", descripcion="Tapa de CPLA (bioplástico resistente al calor) con boquilla para beber cómodamente. Ajuste seguro para evitar derrames.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add_all([RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Tamaño Compatible", orden=1, opciones=['8oz', '12oz']), RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Color", orden=2, opciones=['Blanco', 'Negro'])])
        db.session.commit()
        for price_point in generate_price_breaks("55"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño Compatible': '8oz', 'Color': 'Negro'}, **price_point))
        for price_point in generate_price_breaks("65"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Tamaño Compatible': '12oz', 'Color': 'Negro'}, **price_point))

        # Producto 3: Removedores de Madera
        p = Producto(proveedor_id=prov_id, nombre_producto="Removedores de Madera de Abedul", categoria="Desechables y Packaging", descripcion="Removedores de madera pulida, 100% biodegradables y compostables. Una alternativa elegante y ecológica al plástico.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 1000 unidades', 'Caja 5000 unidades']))
        db.session.commit()
        for price_point in generate_price_breaks("5990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 1000 unidades'}, **price_point))
        for price_point in generate_price_breaks("25000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 5000 unidades'}, **price_point))

        db.session.commit()
        print("-> Productos para 'Ecologico-Pack' cargados.")

        # =====================================================================
        # CATEGORÍA 7: LIMPIEZA E HIGIENE
        # =====================================================================

        # --- PRODUCTOS PARA "Limpieza Total Pro" ---
        prov_id = providers["Limpieza Total Pro"].proveedor_id

        # Producto 1: Detergente Lavaloza Concentrado
        p = Producto(proveedor_id=prov_id, nombre_producto="Detergente Lavaloza Concentrado Limón", categoria="Limpieza e Higiene", descripcion="Fórmula concentrada de alto rendimiento que elimina la grasa más difícil. Aroma fresco a limón. Biodegradable.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bidón 5L', 'Botella 1L']))
        db.session.commit()
        for price_point in generate_price_breaks("12990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bidón 5L'}, **price_point))
        for price_point in generate_price_breaks("3500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Botella 1L'}, **price_point))

        # Producto 2: Desengrasante Industrial para Cocinas
        p = Producto(proveedor_id=prov_id, nombre_producto="Desengrasante Industrial para Cocinas", categoria="Limpieza e Higiene", descripcion="Potente desengrasante alcalino para la limpieza de campanas, planchas, hornos y superficies con grasa pesada.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bidón 5L', 'Gatillo 900ml']))
        db.session.commit()
        for price_point in generate_price_breaks("18990"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bidón 5L'}, **price_point))
        for price_point in generate_price_breaks("4800"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Gatillo 900ml'}, **price_point))
        
        # Producto 3: Toalla de Papel Interfoliada
        p = Producto(proveedor_id=prov_id, nombre_producto="Toalla de Papel Interfoliada", categoria="Limpieza e Higiene", descripcion="Toallas de papel de hoja doble, de alta absorción y resistencia. Dispensado una a una para mayor higiene y ahorro.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 2000 unidades']))
        db.session.commit()
        for price_point in generate_price_breaks("15500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 2000 unidades'}, **price_point))

        db.session.commit()
        print("-> Productos para 'Limpieza Total Pro' cargados.")
        
        # =====================================================================
        # CATEGORÍA 8: CONGELADOS Y PREPARADOS
        # =====================================================================

        # --- PRODUCTOS PARA "BredenMaster" ---
        prov_id = providers["BredenMaster"].proveedor_id
        
        # Producto 1: Croissant de Mantequilla Congelado
        p = Producto(proveedor_id=prov_id, nombre_producto="Croissant de Mantequilla Pre-fermentado", categoria="Congelados y Preparados", descripcion="Croissants de mantequilla listos para hornear. De la caja al horno para un producto fresco y crujiente en minutos.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 60 unidades']))
        db.session.commit()
        for price_point in generate_price_breaks("35000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 60 unidades'}, **price_point))
        
        # Producto 2: Muffin Congelado
        p = Producto(proveedor_id=prov_id, nombre_producto="Muffin Congelado listo para consumir", categoria="Congelados y Preparados", descripcion="Muffins jugosos y sabrosos. Solo descongela y sirve. Ahorra tiempo y reduce mermas en tu operación.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Sabor", orden=1, opciones=['Chips de Chocolate', 'Arándano']))
        db.session.commit()
        for price_point in generate_price_breaks("22000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Chips de Chocolate'}, **price_point))
        for price_point in generate_price_breaks("23500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Sabor': 'Arándano'}, **price_point))

        # Producto 3: Pan Ciabatta Precocido Congelado
        p = Producto(proveedor_id=prov_id, nombre_producto="Pan Ciabatta Precocido Congelado", categoria="Congelados y Preparados", descripcion="Pan de estilo italiano con corteza crujiente y miga aireada. Termina la cocción en tu horno en solo 8 minutos.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Caja 40 unidades']))
        db.session.commit()
        for price_point in generate_price_breaks("28000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 40 unidades'}, **price_point))
        
        db.session.commit()
        print("-> Productos para 'BredenMaster' cargados.")

        # --- PRODUCTOS PARA "Frutos del Maipo" ---
        prov_id = providers["Frutos del Maipo"].proveedor_id

        # Producto 1: Frutillas Congeladas IQF
        p = Producto(proveedor_id=prov_id, nombre_producto="Frutillas Congeladas IQF", categoria="Congelados y Preparados", descripcion="Frutillas enteras congeladas individualmente (IQF) para que no se peguen. Perfectas para jugos, batidos y postres.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg', 'Caja 5kg']))
        db.session.commit()
        for price_point in generate_price_breaks("4500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        for price_point in generate_price_breaks("21000"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Caja 5kg'}, **price_point))

        # Producto 2: Palta en Mitades Congelada
        p = Producto(proveedor_id=prov_id, nombre_producto="Palta en Mitades Congelada", categoria="Congelados y Preparados", descripcion="Palta Hass en su punto, pelada y en mitades. Disminuye la merma y ten palta de calidad disponible todo el año.")
        db.session.add(p); db.session.commit()
        add_mandatory_reqs(p.producto_id)
        db.session.add(RequisitoProducto(producto_id=p.producto_id, nombre_requisito="Formato", orden=1, opciones=['Bolsa 1kg']))
        db.session.commit()
        for price_point in generate_price_breaks("11500"): db.session.add(PreciosProducto(producto_id=p.producto_id, variante_requisitos={'Formato': 'Bolsa 1kg'}, **price_point))
        
        db.session.commit()
        print("-> Productos para 'Frutos del Maipo' cargados.")



        print("\n=====================================================")
        print("= PROCESO DE SEEDING FINALIZADO EXITOSAMENTE =")
        print("=====================================================")


# Este bloque final asegura que el script pueda ser llamado desde la línea de comandos
if __name__ == '__main__':
    cli()