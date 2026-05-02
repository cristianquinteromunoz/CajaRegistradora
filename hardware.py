import win32print
from datetime import datetime
import database


# ==========================================
# MÓDULO DE HARDWARE - KURO SYSTEMS V2
# Configurado para Impresora Térmica 58mm (32 Caracteres)
# ==========================================

def enviar_raw_impresora(datos_bytes):
    """
    Inyecta los datos crudos (RAW) directamente al hardware
    saltándose la cola de renderizado de Windows para máxima velocidad.
    """
    try:
        # Obtiene la impresora térmica que esté como predeterminada en Windows
        nombre_impresora = win32print.GetDefaultPrinter()
        hImpresora = win32print.OpenPrinter(nombre_impresora)
        try:
            hJob = win32print.StartDocPrinter(hImpresora, 1, ("Kuro_Ticket", None, "RAW"))
            win32print.StartPagePrinter(hImpresora)

            # Envía los bytes (texto codificado o pulsos eléctricos)
            win32print.WritePrinter(hImpresora, datos_bytes)

            win32print.EndPagePrinter(hImpresora)
            win32print.EndDocPrinter(hImpresora)
        finally:
            win32print.ClosePrinter(hImpresora)
    except Exception as e:
        print(f"[Hardware] -> Error de comunicación con impresora: {e}")


def abrir_cajon():
    """
    Envía el pulso eléctrico ESC/POS para expulsar el cajón monedero RJ11.
    """
    try:
        # Pulso universal para la mayoría de impresoras térmicas
        pulso_cajon = b'\x1B\x70\x00\x19\xFA'
        print("\n[Hardware] -> 🔊 ENVIANDO PULSO AL CAJÓN MONEDERO...")
        enviar_raw_impresora(pulso_cajon)
    except Exception as e:
        print(f"[Hardware] -> Falló la apertura del cajón: {e}")


def generar_ticket_impresion(venta_id, carrito, total, recibido, cambio, metodo, cajero):
    """
    Genera el ticket en formato de 3 columnas (32 caracteres de ancho)
    y lo envía a la impresora.
    """
    # 1. RECUPERAR CONFIGURACIÓN DESDE TU NUEVA BASE DE DATOS
    config = database.obtener_configuracion()

    # Extraemos los valores del diccionario (con valores por defecto por si acaso)
    nombre_empresa = config.get("empresa", "MI TIENDA")
    nit_empresa = config.get("nit", "NIT: 000000000-0")
    dir_empresa = config.get("direccion", "Cali, Valle del Cauca")
    tel_empresa = config.get("telefono", "Tel: 0000000")
    pie_pagina = config.get("mensaje", "Gracias por su compra")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 2. CONSTRUCCIÓN DEL TICKET (Máximo 32 caracteres)
    # .center(32) centra el texto matemáticamente en el papel de 58mm
    ticket = f"{nombre_empresa.center(32)}\n"
    ticket += f"{nit_empresa.center(32)}\n"
    ticket += f"{dir_empresa.center(32)}\n"
    ticket += f"{tel_empresa.center(32)}\n"
    ticket += "-" * 32 + "\n"
    ticket += f"Ticket: #{venta_id}\n"
    ticket += f"Fecha:  {fecha}\n"
    ticket += f"Cajero: {cajero.upper()}\n"
    ticket += "-" * 32 + "\n"

    # Cabecera de tabla (Cant: 5, Desc: 16, Precio: 9 -> Total 30 + 2 espacios = 32)
    ticket += f"{'Cant':<5} {'Descripción':<16} {'Precio':>9}\n"
    ticket += "-" * 32 + "\n"

    # 3. LISTADO DE PRODUCTOS
    for item in carrito:
        nombre_limpio = item['nombre'][:15]  # Recorte de seguridad
        cant_txt = f"{item['cantidad']:g}"
        precio_txt = f"{int(item['subtotal']):,}".replace(",", ".")

        ticket += f"{cant_txt:<5} {nombre_limpio:<16} {precio_txt:>9}\n"

    # 4. TOTALES Y PIE DE PÁGINA
    ticket += "-" * 32 + "\n"
    ticket += f"TOTAL:           $ {int(total):,}\n".replace(",", ".")
    ticket += f"Método:          {metodo}\n"

    if metodo == "Efectivo":
        ticket += f"Recibido:        $ {int(recibido):,}\n".replace(",", ".")
        ticket += f"Cambio:          $ {int(cambio):,}\n".replace(",", ".")

    ticket += "-" * 32 + "\n"
    ticket += f"{pie_pagina.center(32)}\n"

    # Saltos de línea para que el papel salga de la ranura de corte
    ticket += "\n\n\n\n\n"

    # 5. CODIFICACIÓN Y ENVÍO FÍSICO
    print(ticket)  # Para que lo veas en la consola mientras desarrollas
    print("\n--- ENVIANDO DATOS AL PUERTO DE LA IMPRESORA ---")

    try:
        # cp850 codifica correctamente la Ñ y las tildes para impresoras térmicas
        ticket_bytes = ticket.encode('cp850', errors='replace')

        # Comando para corte automático (Si tu impresora tiene guillotina)
        corte_papel = b'\x1D\x56\x42\x00'

        # Enviamos ticket + instrucción de corte
        enviar_raw_impresora(ticket_bytes + corte_papel)

    except Exception as e:
        print(f"[Hardware] -> Fallo en la codificación o envío: {e}")

    return ticket