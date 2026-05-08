import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "kuro_inventario.db"

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def inicializar_bd():
    with sqlite3.connect(DB_NAME) as conexion:
        cursor = conexion.cursor()

        tablas = [
            '''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_barras TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, precio_compra REAL NOT NULL, precio_venta REAL NOT NULL, stock REAL NOT NULL)''',
            '''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, rol TEXT NOT NULL, nombre_completo TEXT, documento TEXT, telefono TEXT, correo TEXT)''',
            '''CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, cajero TEXT NOT NULL, total REAL NOT NULL)''',
            '''CREATE TABLE IF NOT EXISTS detalles_venta (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, codigo_producto TEXT, nombre_producto TEXT, cantidad REAL, precio_unitario REAL, subtotal REAL, FOREIGN KEY(venta_id) REFERENCES ventas(id))''',
            '''CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, categoria TEXT NOT NULL, descripcion TEXT, monto REAL NOT NULL, usuario TEXT NOT NULL)''',
            '''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)'''
        ]
        for query in tablas: cursor.execute(query)

        migraciones = [
            "ALTER TABLE productos ADD COLUMN fecha_modificacion TEXT",
            "ALTER TABLE productos ADD COLUMN stock_minimo REAL DEFAULT 5",
            "ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT",
            "ALTER TABLE usuarios ADD COLUMN documento TEXT",
            "ALTER TABLE usuarios ADD COLUMN telefono TEXT",
            "ALTER TABLE usuarios ADD COLUMN correo TEXT",
            "ALTER TABLE ventas ADD COLUMN efectivo REAL DEFAULT 0",
            "ALTER TABLE ventas ADD COLUMN cambio REAL DEFAULT 0",
            "ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'",
            "ALTER TABLE detalles_venta ADD COLUMN costo_unitario REAL DEFAULT 0",
            "ALTER TABLE gastos ADD COLUMN frecuencia TEXT DEFAULT 'Diario'",
            "ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'",
            "ALTER TABLE detalles_venta ADD COLUMN categoria TEXT DEFAULT 'General'",
            "ALTER TABLE productos ADD COLUMN es_fraccion INTEGER DEFAULT 0",
            # NUEVAS MIGRACIONES: Mayoreo, Fracción y Caducidad
            "ALTER TABLE productos ADD COLUMN precio_mayoreo REAL DEFAULT 0",
            "ALTER TABLE productos ADD COLUMN cantidad_mayoreo REAL DEFAULT 0",
            "ALTER TABLE productos ADD COLUMN precio_fraccion REAL DEFAULT 0",
            "ALTER TABLE productos ADD COLUMN fecha_caducidad TEXT"
            "ALTER TABLE productos ADD COLUMN precio_fraccion REAL DEFAULT 0",
            "ALTER TABLE productos ADD COLUMN fecha_caducidad TEXT",
            "ALTER TABLE productos ADD COLUMN divisor_fraccion REAL DEFAULT 1"
        ]
        for m in migraciones:
            try: cursor.execute(m)
            except sqlite3.OperationalError: pass

        cursor.execute("SELECT COUNT(*) FROM configuracion")
        if cursor.fetchone()[0] == 0:
            config_inicial = [("empresa", "KURO SYSTEMS"), ("nit", "NIT: 900.000.000-1"), ("direccion", "Cali, Valle del Cauca"), ("telefono", "Tel: 300 000 0000"), ("mensaje", "¡Gracias por su compra!")]
            cursor.executemany("INSERT INTO configuracion (clave, valor) VALUES (?, ?)", config_inicial)

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo) VALUES (?, ?, ?, ?)", ("admin", encriptar_password("admin123"), "admin", "Administrador Principal"))
        conexion.commit()

def verificar_login(username, password_plana):
    with sqlite3.connect(DB_NAME) as conexion:
        res = conexion.execute("SELECT rol FROM usuarios WHERE username = ? AND password_hash = ?", (username, encriptar_password(password_plana))).fetchone()
        return (True, res[0]) if res else (False, None)

def obtener_configuracion():
    with sqlite3.connect(DB_NAME) as conexion:
        return {f[0]: f[1] for f in conexion.execute("SELECT clave, valor FROM configuracion").fetchall()}

def actualizar_configuracion(empresa, nit, direccion, telefono, mensaje):
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            conexion.executemany("UPDATE configuracion SET valor = ? WHERE clave = ?", [(empresa, "empresa"), (nit, "nit"), (direccion, "direccion"), (telefono, "telefono"), (mensaje, "mensaje")])
            conexion.commit(); return True, "Ajustes guardados."
    except Exception as e: return False, str(e)

def crear_usuario(usr, pwd, rol, nom, doc, tel, correo):
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            conexion.execute('INSERT INTO usuarios (username, password_hash, rol, nombre_completo, documento, telefono, correo) VALUES (?, ?, ?, ?, ?, ?, ?)', (usr.lower(), encriptar_password(pwd), rol, nom, doc, tel, correo))
            return True, "Usuario creado exitosamente."
    except sqlite3.IntegrityError: return False, "El usuario ya existe."

def obtener_usuarios():
    with sqlite3.connect(DB_NAME) as conexion:
        return conexion.execute("SELECT username, rol, nombre_completo, documento, telefono FROM usuarios").fetchall()

def eliminar_usuario(username):
    if username == "admin": return False, "Admin no se puede borrar."
    with sqlite3.connect(DB_NAME) as conexion:
        conexion.execute("DELETE FROM usuarios WHERE username = ?", (username,)); return True, "Usuario eliminado."

# --- INVENTARIO AVANZADO ---
def obtener_categorias():
    with sqlite3.connect(DB_NAME) as conexion:
        filas = conexion.execute("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL ORDER BY categoria").fetchall()
        return [f[0] for f in filas if f[0].strip() != ""]

def obtener_alertas_stock():
    with sqlite3.connect(DB_NAME) as conexion:
        return conexion.execute("SELECT codigo_barras, nombre, stock, stock_minimo FROM productos WHERE stock <= stock_minimo").fetchall()

def obtener_alertas_caducidad():
    from datetime import datetime, timedelta
    alertas = []
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            filas = conexion.execute("SELECT codigo_barras, nombre, fecha_caducidad FROM productos WHERE fecha_caducidad IS NOT NULL AND fecha_caducidad != ''").fetchall()
            hoy = datetime.now()
            limite = hoy + timedelta(days=30) # Te avisa con 30 días de anticipación

            for cod, nom, fecha_str in filas:
                try:
                    # Soporta que el usuario escriba AAAA-MM-DD o DD/MM/AAAA
                    if "-" in fecha_str: f_cad = datetime.strptime(fecha_str, "%Y-%m-%d")
                    elif "/" in fecha_str: f_cad = datetime.strptime(fecha_str, "%d/%m/%Y")
                    else: continue

                    if f_cad <= limite:
                        dias = (f_cad - hoy).days
                        if dias < 0: estado = f"¡VENCIDO! (Hace {abs(dias)} días)"
                        elif dias == 0: estado = "¡Vence HOY!"
                        else: estado = f"Vence en {dias} días"
                        alertas.append((cod, nom, fecha_str, estado))
                except: pass
    except: pass
    return alertas

def agregar_producto(cod, nom, cat, pre_c, pre_v, stk, stk_min, es_frac, p_may, c_may, p_frac, f_cad, div_frac):
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            conexion.execute('''INSERT INTO productos 
                (codigo_barras, nombre, categoria, precio_compra, precio_venta, stock, fecha_modificacion, stock_minimo, es_fraccion, precio_mayoreo, cantidad_mayoreo, precio_fraccion, fecha_caducidad, divisor_fraccion) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (cod, nom, cat, pre_c, pre_v, stk, fecha, stk_min, es_frac, p_may, c_may, p_frac, f_cad, div_frac))
            return True, "Producto guardado."
    except sqlite3.IntegrityError: return False, "Código duplicado."

def buscar_productos(codigo="", nombre=""):
    with sqlite3.connect(DB_NAME) as conexion:
        return conexion.execute('SELECT codigo_barras, nombre, categoria, precio_compra, precio_venta, stock, stock_minimo, fecha_caducidad, es_fraccion FROM productos WHERE codigo_barras LIKE ? AND nombre LIKE ?', (f'%{codigo}%', f'%{nombre}%')).fetchall()

def actualizar_producto(cod, nom, cat, pre_c, pre_v, stk, stk_min, es_frac, p_may, c_may, p_frac, f_cad, div_frac):
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            conexion.execute('''UPDATE productos SET 
                nombre=?, categoria=?, precio_compra=?, precio_venta=?, stock=?, stock_minimo=?, fecha_modificacion=?, es_fraccion=?, 
                precio_mayoreo=?, cantidad_mayoreo=?, precio_fraccion=?, fecha_caducidad=?, divisor_fraccion=? 
                WHERE codigo_barras=?''',
                (nom, cat, pre_c, pre_v, stk, stk_min, fecha, es_frac, p_may, c_may, p_frac, f_cad, div_frac, cod))
            return True, "Producto actualizado."
    except Exception as e: return False, str(e)

def eliminar_producto(codigo):
    with sqlite3.connect(DB_NAME) as conexion:
        conexion.execute("DELETE FROM productos WHERE codigo_barras = ?", (codigo,)); return True, "Eliminado"

# --- FACTURACIÓN Y FINANZAS ---
def buscar_producto_exacto(codigo):
    with sqlite3.connect(DB_NAME) as conexion:
        # Añadimos divisor_fraccion al final del SELECT
        return conexion.execute("SELECT codigo_barras, nombre, precio_venta, stock, precio_compra, categoria, es_fraccion, precio_mayoreo, cantidad_mayoreo, precio_fraccion, fecha_caducidad, divisor_fraccion FROM productos WHERE codigo_barras = ?", (codigo,)).fetchone()


def registrar_venta(carrito, total, cajero, efectivo, cambio, metodo_pago):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO ventas (fecha, cajero, total, efectivo, cambio, metodo_pago) VALUES (?, ?, ?, ?, ?, ?)",
            (fecha, cajero, total, efectivo, cambio, metodo_pago)
        )
        venta_id = cursor.lastrowid

        for item in carrito:
            cursor.execute(
                '''INSERT INTO detalles_venta (venta_id, codigo_producto, nombre_producto, cantidad, precio_unitario,
                                               subtotal, costo_unitario, categoria)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (venta_id, item['codigo'], item['nombre'], item['cantidad'], item['precio_usado'], item['subtotal'],
                 item['costo'], item['categoria'])
            )

            # Cálculo de la fracción para restar del inventario
            if item.get('modo_fraccion', False):
                divisor = item.get('divisor_fraccion', 1.0)
                if divisor <= 0:
                    divisor = 1.0
                stock_a_restar = item['cantidad'] / divisor
            else:
                stock_a_restar = item['cantidad']

            cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE codigo_barras = ?",
                (stock_a_restar, item['codigo'])
            )

        conexion.commit()
        return True, venta_id

    except Exception as e:
        conexion.rollback()
        return False, str(e)

    finally:
        conexion.close()

def obtener_ventas_por_fecha(fecha):
    with sqlite3.connect(DB_NAME) as conexion: return conexion.execute("SELECT id, fecha, cajero, total, efectivo, cambio, metodo_pago FROM ventas WHERE fecha LIKE ?", (f"{fecha}%",)).fetchall()

def obtener_venta_por_id(venta_id):
    with sqlite3.connect(DB_NAME) as conexion: return conexion.execute("SELECT id, fecha, cajero, total, efectivo, cambio, metodo_pago FROM ventas WHERE id = ?", (venta_id,)).fetchone()

def obtener_detalles_venta(venta_id):
    with sqlite3.connect(DB_NAME) as conexion: return conexion.execute("SELECT codigo_producto, nombre_producto, cantidad, precio_unitario, subtotal FROM detalles_venta WHERE venta_id = ?", (venta_id,)).fetchall()

def anular_venta(venta_id):
    conexion = sqlite3.connect(DB_NAME); cursor = conexion.cursor()
    try:
        detalles = cursor.execute("SELECT codigo_producto, cantidad FROM detalles_venta WHERE venta_id = ?", (venta_id,)).fetchall()
        for cod, cant in detalles: cursor.execute("UPDATE productos SET stock = stock + ? WHERE codigo_barras = ?", (cant, cod))
        cursor.execute("DELETE FROM detalles_venta WHERE venta_id = ?", (venta_id,))
        cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
        conexion.commit(); return True, "Venta anulada. Inventario y finanzas corregidas."
    except Exception as e: conexion.rollback(); return False, f"Error al anular: {str(e)}"
    finally: conexion.close()

def registrar_gasto(cat, frec, desc, monto, usuario):
    try:
        with sqlite3.connect(DB_NAME) as conexion:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conexion.execute("INSERT INTO gastos (fecha, categoria, frecuencia, descripcion, monto, usuario) VALUES (?, ?, ?, ?, ?, ?)", (fecha, cat, frec, desc, monto, usuario))
            return True, "Gasto registrado."
    except Exception as e: return False, str(e)

def obtener_gastos(f_ini, f_fin):
    with sqlite3.connect(DB_NAME) as conexion: return conexion.execute("SELECT fecha, categoria, frecuencia, descripcion, monto, usuario FROM gastos WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC", (f"{f_ini} 00:00:00", f"{f_fin} 23:59:59")).fetchall()

def generar_cierre_diario(fecha):
    with sqlite3.connect(DB_NAME) as conexion:
        cursor = conexion.cursor()
        efectivo = cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha LIKE ? AND metodo_pago = 'Efectivo'", (f"{fecha}%",)).fetchone()[0] or 0.0
        pagos_electronicos = cursor.execute("SELECT metodo_pago, SUM(total) FROM ventas WHERE fecha LIKE ? AND metodo_pago != 'Efectivo' GROUP BY metodo_pago", (f"{fecha}%",)).fetchall()
        total_electronico = sum([p[1] for p in pagos_electronicos])
        categorias_ventas = cursor.execute('''SELECT categoria, SUM(subtotal) FROM detalles_venta dv JOIN ventas v ON dv.venta_id = v.id WHERE v.fecha LIKE ? GROUP BY categoria''', (f"{fecha}%",)).fetchall()
        cajeros = cursor.execute("SELECT DISTINCT cajero FROM ventas WHERE fecha LIKE ?", (f"{fecha}%",)).fetchall()
        gastos_diarios_lista = cursor.execute("SELECT categoria, descripcion, monto FROM gastos WHERE fecha LIKE ? AND frecuencia = 'Diario'", (f"{fecha}%",)).fetchall()
        gastos_diarios_total = sum([g[2] for g in gastos_diarios_lista])
        mes = fecha[:7]
        gastos_mensuales = cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha LIKE ? AND frecuencia = 'Mensual'", (f"{mes}%",)).fetchone()[0] or 0.0
        gasto_fijo_diario = gastos_mensuales / 30.0
        costo_mercancia = cursor.execute("SELECT SUM(dv.cantidad * dv.costo_unitario) FROM detalles_venta dv JOIN ventas v ON dv.venta_id = v.id WHERE v.fecha LIKE ?", (f"{fecha}%",)).fetchone()[0] or 0.0
        ganancia = (efectivo + total_electronico) - costo_mercancia - gastos_diarios_total - gasto_fijo_diario
        return {"total_ingresos": efectivo + total_electronico, "efectivo": efectivo, "desglose_electronico": pagos_electronicos, "categorias": categorias_ventas, "cajeros": [c[0].upper() for c in cajeros], "salidas_detalle": gastos_diarios_lista, "total_salidas": gastos_diarios_total, "fijo_diario": gasto_fijo_diario, "ganancia_neta": ganancia}

def generar_reporte_financiero(f_ini, f_fin):
    with sqlite3.connect(DB_NAME) as conexion:
        cursor = conexion.cursor()
        ini, fin = f"{f_ini} 00:00:00", f"{f_fin} 23:59:59"
        efectivo = cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha BETWEEN ? AND ? AND metodo_pago = 'Efectivo'", (ini, fin)).fetchone()[0] or 0.0
        electronico = cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha BETWEEN ? AND ? AND metodo_pago != 'Efectivo'", (ini, fin)).fetchone()[0] or 0.0
        costo_mercancia = cursor.execute("SELECT SUM(dv.cantidad * dv.costo_unitario) FROM detalles_venta dv JOIN ventas v ON dv.venta_id = v.id WHERE v.fecha BETWEEN ? AND ?", (ini, fin)).fetchone()[0] or 0.0
        dias_rango = max(1, (datetime.strptime(f_fin, '%Y-%m-%d') - datetime.strptime(f_ini, '%Y-%m-%d')).days + 1)
        gastos_diarios = cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha BETWEEN ? AND ? AND frecuencia = 'Diario'", (ini, fin)).fetchone()[0] or 0.0
        gastos_mensuales_mes = cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha LIKE ? AND frecuencia = 'Mensual'", (f"{f_ini[:7]}%",)).fetchone()[0] or 0.0
        gastos_totales = gastos_diarios + ((gastos_mensuales_mes / 30.0) * dias_rango)
        return {"ventas_totales": efectivo + electronico, "efectivo_caja": efectivo, "pagos_electronicos": electronico, "costo_mercancia": costo_mercancia, "gastos_operativos": gastos_totales, "ganancia_neta": (efectivo + electronico) - costo_mercancia - gastos_totales}