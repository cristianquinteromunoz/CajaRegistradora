import customtkinter as ctk
from tkinter import ttk, messagebox
import theme
import database
import hardware
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
from datetime import datetime, timedelta


# --- CLASE BASE ---
class ViewBase(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.pack(fill="both", expand=True)


# ==========================================
# 1. PANTALLA DE LOGIN
# ==========================================
class LoginView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=15, fg_color=theme.COLORS["bg_card"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="KURO\nSYSTEMS", font=theme.FONTS["h1"], text_color=theme.COLORS["text_main"]).pack(
            pady=(40, 20))

        self.ent_user = ctk.CTkEntry(frame, placeholder_text="Usuario", width=250, height=40)
        self.ent_user.pack(pady=10)
        self.ent_user.bind("<Return>", lambda e: self.intentar_login())

        self.ent_pass = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=250, height=40)
        self.ent_pass.pack(pady=10)
        self.ent_pass.bind("<Return>", lambda e: self.intentar_login())

        self.lbl_error = ctk.CTkLabel(frame, text="", text_color=theme.COLORS["danger"])
        self.lbl_error.pack(pady=5)

        ctk.CTkButton(frame, text="Ingresar", height=40, width=250, font=theme.FONTS["body_bold"],
                      fg_color=theme.COLORS["primary"], hover_color=theme.COLORS["primary_hover"],
                      command=self.intentar_login).pack(pady=20)

    def intentar_login(self):
        if not self.app.procesar_login(self.ent_user.get(), self.ent_pass.get()):
            self.lbl_error.configure(text="Credenciales incorrectas o campos vacíos.")


# ==========================================
# 2. SISTEMA MULTICAJA (CONTENEDOR DE PESTAÑAS)
# ==========================================
class POSView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)

        # Gestor de pestañas
        self.tabs = ctk.CTkTabview(self, command=self.al_cambiar_pestana)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=0)

        self.terminales = {}
        for nombre in ["Caja 1", "Caja 2 (En Espera)", "Caja 3 (En Espera)"]:
            tab = self.tabs.add(nombre)
            # Creamos una terminal 100% independiente para cada pestaña
            terminal = POSInstance(tab, app)
            terminal.pack(fill="both", expand=True)
            self.terminales[nombre] = terminal

    def al_cambiar_pestana(self):
        # Auto-enfoca el buscador de la pestaña activa para facturar rápidamente
        tab_activa = self.tabs.get()
        if tab_activa in self.terminales:
            self.terminales[tab_activa].ent_codigo.focus()

    def enfocar_caja(self):
        self.al_cambiar_pestana()


# ==========================================
# 2.1. INSTANCIA INDIVIDUAL DE LA CAJA (Antes POSView)
# ==========================================
class POSInstance(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.carrito = []
        self.total_venta = 0.0
        self.cambio_actual = 0.0

        # ==========================================
        # 1. CABECERA
        # ==========================================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="Terminal de Venta", font=theme.FONTS["h1"]).pack(side="left")

        caja_admin = ctk.CTkFrame(header, fg_color="transparent")
        caja_admin.pack(side="right")
        ctk.CTkLabel(caja_admin, text=f"Cajero: {self.app.rol_actual.upper()}", text_color=theme.COLORS["warning"],
                     font=theme.FONTS["body_bold"]).pack(side="right", padx=(15, 0))
        ctk.CTkButton(caja_admin, text="📊 Cierre", width=60, fg_color="#34495E", hover_color="#2C3E50",
                      command=self.abrir_cierre_caja).pack(side="right", padx=5)
        ctk.CTkButton(caja_admin, text="📜 Historial", width=60, fg_color=theme.COLORS["special"],
                      hover_color=theme.COLORS["special_hover"], command=self.abrir_historial).pack(side="right",
                                                                                                    padx=5)

        # ==========================================
        # 2. BARRA DE BÚSQUEDA Y CARRITO
        # ==========================================
        search = ctk.CTkFrame(self, corner_radius=10, fg_color=theme.COLORS["bg_card"])
        search.pack(fill="x", padx=20, pady=5)

        self.ent_codigo = ctk.CTkEntry(search, width=250, height=40, font=theme.FONTS["h3"],
                                       placeholder_text="Escanear o digitar código...")
        self.ent_codigo.pack(side="left", padx=15, pady=15)
        self.ent_codigo.bind("<Return>", lambda e: self.add_carrito())
        self.ent_codigo.focus()

        ctk.CTkButton(search, text="🔍 Buscar", width=70, height=40, fg_color=theme.COLORS["primary"],
                      command=self.abrir_buscador).pack(side="left", padx=5)
        ctk.CTkButton(search, text="➕ Libre", width=70, height=40, fg_color="#E67E22", hover_color="#D35400",
                      command=self.abrir_venta_libre).pack(side="left", padx=5)

        ctk.CTkButton(search, text="🗑️ Eliminar", fg_color=theme.COLORS["danger"],
                      hover_color=theme.COLORS["danger_hover"],
                      font=theme.FONTS["h3"], width=40, height=40, command=self.quitar_item).pack(side="right",
                                                                                                  padx=(5, 15))
        ctk.CTkButton(search, text="✏️ Cantidad", fg_color=theme.COLORS["warning"],
                      hover_color=theme.COLORS["warning_hover"], font=theme.FONTS["body_bold"], width=60, height=40,
                      command=self.cambiar_cant).pack(side="right", padx=5)
        ctk.CTkButton(search, text="📦 Mayor", fg_color="#2980B9", hover_color="#3498DB", font=theme.FONTS["body_bold"],
                      width=60, height=40, command=self.aplicar_precio_mayoreo).pack(side="right", padx=5)
        ctk.CTkButton(search, text="🧩 Frac", fg_color="#8E44AD", hover_color="#9B59B6", font=theme.FONTS["body_bold"],
                      width=60, height=40, command=self.aplicar_precio_fraccion).pack(side="right", padx=5)

        # ==========================================
        # 3. TABLA Y PIE DE PÁGINA
        # ==========================================
        tb_frame = ctk.CTkFrame(self, fg_color="transparent")
        tb_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabla = ttk.Treeview(tb_frame, columns=("codigo", "nombre", "precio", "cantidad", "subtotal"),
                                  show="headings", height=8)
        for col, txt, w in [("codigo", "Código", 100), ("nombre", "Artículo", 350), ("precio", "Precio Unit.", 100),
                            ("cantidad", "Cant.", 80), ("subtotal", "Subtotal", 120)]:
            self.tabla.heading(col, text=txt)
            self.tabla.column(col, width=w, anchor="w" if col == "nombre" else "center")

        self.tabla.tag_configure('impar', background=theme.COLORS["table_odd"])
        self.tabla.tag_configure('par', background=theme.COLORS["table_even"])
        self.tabla.tag_configure('fraccion', background="#4A235A", foreground="white")
        self.tabla.tag_configure('temporal', background="#7E5109", foreground="white")
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(tb_frame, orientation="vertical", command=self.tabla.yview)
        scrollbar.pack(side="right", fill="y", padx=(5, 0))
        self.tabla.configure(yscrollcommand=scrollbar.set)

        bot = ctk.CTkFrame(self, fg_color=theme.COLORS["table_header"], corner_radius=10)
        bot.pack(fill="x", padx=20, pady=15)
        self.lbl_total = ctk.CTkLabel(bot, text="Total: $ 0", font=("Arial", 36, "bold"),
                                      text_color=theme.COLORS["success"])
        self.lbl_total.pack(side="left", padx=20, pady=20)

        caja = ctk.CTkFrame(bot, fg_color="transparent")
        caja.pack(side="left", padx=30)
        ctk.CTkLabel(caja, text="Método de Pago:", font=theme.FONTS["body"],
                     text_color=theme.COLORS["text_muted"]).pack(anchor="w")
        self.op_pago = ctk.CTkOptionMenu(caja, values=["Efectivo", "Tarjeta", "Transferencia", "Nequi"],
                                         command=self.gestionar_pago)
        self.op_pago.pack(pady=(0, 10), fill="x")

        din = ctk.CTkFrame(caja, fg_color="transparent")
        din.pack(fill="x")
        self.ent_efectivo = ctk.CTkEntry(din, width=120, height=35, font=theme.FONTS["h3"],
                                         placeholder_text="Recibido...")
        self.ent_efectivo.pack(side="left", padx=(0, 10))
        self.ent_efectivo.bind("<KeyRelease>", self.calc_cambio)
        self.lbl_cambio = ctk.CTkLabel(din, text="Cambio: $ 0", font=theme.FONTS["h3"],
                                       text_color=theme.COLORS["text_highlight"])
        self.lbl_cambio.pack(side="left")

        ctk.CTkButton(bot, text="✅ FACTURAR", font=theme.FONTS["h3"], fg_color=theme.COLORS["success"],
                      hover_color=theme.COLORS["success_hover"], height=65, width=220, command=self.procesar).pack(
            side="right", padx=20, pady=20)

        self.chk_imprimir = ctk.CTkCheckBox(bot, text="🖨️ Recibo", font=theme.FONTS["body_bold"],
                                            text_color=theme.COLORS["text_main"])
        self.chk_imprimir.pack(side="right", padx=15)
        self.chk_imprimir.select()

    # --- LÓGICA DE LA CAJA (Idéntica a la anterior) ---
    def abrir_venta_libre(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Venta Libre / Artículo Temporal")
        popup.geometry("400x300")
        popup.transient(self)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Descripción del Artículo/Servicio:", font=theme.FONTS["body_bold"]).pack(pady=(20, 5))
        ent_nom = ctk.CTkEntry(popup, width=300, height=35)
        ent_nom.pack(pady=5)
        ent_nom.insert(0, "Artículo Varios")

        ctk.CTkLabel(popup, text="Precio Total ($):", font=theme.FONTS["body_bold"]).pack(pady=(15, 5))
        ent_pre = ctk.CTkEntry(popup, width=300, height=35)
        ent_pre.pack(pady=5)
        ent_pre.focus()

        def agregar(e=None):
            val = ent_pre.get().replace(",", ".").strip()
            if not val: return
            try:
                precio = float(val)
                if precio < 0: return messagebox.showerror("Error", "El precio no puede ser negativo.")
                nom = ent_nom.get().strip().upper() or "ARTÍCULO VARIOS"
                self.carrito.append({
                    'codigo': 'TEMP', 'nombre': nom, 'costo': 0, 'categoria': 'Venta Libre',
                    'precio_normal': precio, 'precio_mayoreo': 0, 'cantidad_mayoreo': 0,
                    'es_fraccion': True, 'precio_fraccion': 0, 'modo_fraccion': False, 'modo_mayoreo_manual': False,
                    'cantidad': 1, 'precio_usado': precio, 'subtotal': precio
                })
                self.actualizar_ui()
                popup.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un precio válido usando números.")

        ent_pre.bind("<Return>", agregar)
        ctk.CTkButton(popup, text="Añadir a Factura", fg_color=theme.COLORS["success"], font=theme.FONTS["body_bold"],
                      height=40, command=agregar).pack(pady=25)

    def calcular_precios_y_subtotales(self):
        for item in self.carrito:
            if item.get('modo_fraccion', False):
                item['precio_usado'] = item['precio_fraccion']
                item['subtotal'] = item['cantidad'] * item['precio_usado']
                continue
            if item.get('modo_mayoreo_manual', False):
                item['precio_usado'] = item['precio_mayoreo']
                item['subtotal'] = item['cantidad'] * item['precio_usado']
                continue
            item['precio_usado'] = item['precio_normal']
            item['subtotal'] = item['cantidad'] * item['precio_usado']

    def aplicar_precio_mayoreo(self):
        sel = self.tabla.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione un artículo de la lista.")
        idx = self.tabla.index(sel[0])
        item = self.carrito[idx]

        if item['codigo'] == 'TEMP': return messagebox.showerror("Bloqueo",
                                                                 "No se puede aplicar mayoreo a una Venta Libre.")
        if item['precio_mayoreo'] <= 0: return messagebox.showerror("Bloqueo",
                                                                    "Este producto no tiene configurado un precio de mayoreo en el inventario.")

        item['modo_mayoreo_manual'] = not item.get('modo_mayoreo_manual', False)
        if item['modo_mayoreo_manual']: item['modo_fraccion'] = False
        self.actualizar_ui()

    def aplicar_precio_fraccion(self):
        sel = self.tabla.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione un artículo de la lista.")
        idx = self.tabla.index(sel[0])
        item = self.carrito[idx]

        if item['codigo'] == 'TEMP': return messagebox.showerror("Bloqueo", "No se puede fraccionar una Venta Libre.")
        if not item['es_fraccion']: return messagebox.showerror("Bloqueo",
                                                                f"El producto '{item['nombre']}' no está configurado para venta por fracción en el inventario.")
        if item['precio_fraccion'] <= 0: return messagebox.showerror("Bloqueo",
                                                                     "Este producto no tiene asignado un precio de fracción en el inventario.")

        item['modo_fraccion'] = not item.get('modo_fraccion', False)
        if item['modo_fraccion']: item['modo_mayoreo_manual'] = False
        self.actualizar_ui()

    def add_carrito(self):
        cod = self.ent_codigo.get().strip()
        self.ent_codigo.delete(0, 'end')
        if not cod: return
        prod = database.buscar_producto_exacto(cod)
        if not prod: return messagebox.showwarning("Error", f"Código '{cod}' no existe.")

        enc = False
        for item in self.carrito:
            if item['codigo'] == prod[0]:

                # --- CORRECCIÓN: Validar stock considerando si es fracción ---
                divisor = item.get('divisor_fraccion', 1.0)
                if divisor <= 0: divisor = 1.0

                stock_requerido = (item['cantidad'] + 1) / divisor if item.get('modo_fraccion', False) else (
                            item['cantidad'] + 1)

                if stock_requerido > prod[3]:
                    if item.get('modo_fraccion', False):
                        return messagebox.showerror("Stock", f"Solo hay {prod[3]:g} enteros disponibles.")
                    else:
                        return messagebox.showerror("Stock", f"Solo hay {prod[3]:g} disponibles.")

                item['cantidad'] += 1
                enc = True
                break

        if not enc:
            if prod[3] < 1: return messagebox.showerror("Agotado", "Producto agotado.")

            divisor_f = prod[11] if len(prod) > 11 and prod[11] else 1.0

            self.carrito.append({
                'codigo': prod[0], 'nombre': prod[1], 'costo': prod[4], 'categoria': prod[5],
                'precio_normal': prod[2], 'precio_mayoreo': prod[7], 'cantidad_mayoreo': prod[8],
                'es_fraccion': prod[6] == 1, 'precio_fraccion': prod[9], 'modo_fraccion': False,
                'modo_mayoreo_manual': False, 'divisor_fraccion': divisor_f,
                'cantidad': 1.0 if prod[6] == 1 else 1, 'precio_usado': prod[2], 'subtotal': prod[2]
            })
        self.actualizar_ui()

    def cambiar_cant(self):
        sel = self.tabla.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione un artículo.")
        idx = self.tabla.index(sel[0])
        item = self.carrito[idx]

        msg_extra = " (Admite decimales, ej. 1.5)" if item['es_fraccion'] else " (Solo números enteros)"
        if item.get('modo_fraccion', False):
            msg_extra = " (Cantidad de FRACCIONES a vender)"

        resp = ctk.CTkInputDialog(text=f"Unidades de '{item['nombre']}'? {msg_extra}", title="Cantidad").get_input()
        if resp:
            try:
                nc = float(resp)
                if nc <= 0: return messagebox.showerror("Error", "Cantidad inválida.")
                if not item['es_fraccion'] and not nc.is_integer(): return messagebox.showerror("Error",
                                                                                                "Este producto no admite decimales.")
                if not item['es_fraccion']: nc = int(nc)

                if item['codigo'] != 'TEMP':
                    disp = database.buscar_producto_exacto(item['codigo'])[3]

                    # --- CORRECCIÓN: Validar stock considerando si está en modo fracción ---
                    divisor = item.get('divisor_fraccion', 1.0)
                    if divisor <= 0: divisor = 1.0

                    stock_requerido = (nc / divisor) if item.get('modo_fraccion', False) else nc

                    if stock_requerido > disp:
                        if item.get('modo_fraccion', False):
                            max_fracciones = int(disp * divisor)
                            return messagebox.showerror("Error",
                                                        f"Stock insuficiente.\nHay {disp:g} enteros disponibles (Alcanza para {max_fracciones} fracciones).")
                        else:
                            return messagebox.showerror("Error", f"Máximo disponible: {disp:g}")

                self.carrito[idx]['cantidad'] = nc
                self.actualizar_ui()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")

    def quitar_item(self):
        if self.tabla.selection():
            del self.carrito[self.tabla.index(self.tabla.selection()[0])]
            self.actualizar_ui()
            self.ent_codigo.focus()

    def actualizar_ui(self):
        self.calcular_precios_y_subtotales()
        for row in self.tabla.get_children(): self.tabla.delete(row)
        self.total_venta = sum(i['subtotal'] for i in self.carrito)

        for i, it in enumerate(self.carrito):
            if it['codigo'] == 'TEMP':
                tag = 'temporal'
                nom_display = f"📝 {it['nombre']}"
            elif it.get('modo_fraccion', False):
                tag = 'fraccion'
                nom_display = f"🧩 {it['nombre']} (Fracción)"
            else:
                tag = 'par' if i % 2 == 0 else 'impar'
                if it.get('modo_mayoreo_manual', False):
                    nom_display = f"⭐ {it['nombre']} (MAYOREO VIP)"
                else:
                    nom_display = it['nombre']

            self.tabla.insert("", "end", values=(it['codigo'], nom_display, f"$ {int(it['precio_usado']):,}",
                                                 f"{it['cantidad']:g}", f"$ {int(it['subtotal']):,}"), tags=(tag,))

        self.lbl_total.configure(text=f"Total: $ {int(self.total_venta):,}".replace(",", "."))
        self.gestionar_pago(self.op_pago.get())

    def gestionar_pago(self, sel):
        if sel == "Efectivo":
            self.ent_efectivo.configure(state="normal")
            self.ent_efectivo.delete(0, 'end')
            self.calc_cambio()
        else:
            self.ent_efectivo.configure(state="normal")
            self.ent_efectivo.delete(0, 'end')
            self.ent_efectivo.insert(0, str(int(self.total_venta)))
            self.ent_efectivo.configure(state="disabled")
            self.lbl_cambio.configure(text="Cambio: $ 0", text_color=theme.COLORS["success"])
            self.cambio_actual = 0.0

    def calc_cambio(self, e=None):
        if self.op_pago.get() != "Efectivo" or self.total_venta == 0: return
        val = self.ent_efectivo.get().replace(".", "").replace(",", "").replace("$", "").strip()
        if not val: self.lbl_cambio.configure(text="Cambio: $ 0",
                                              text_color=theme.COLORS["text_highlight"]); self.cambio_actual = 0; return
        try:
            self.cambio_actual = float(val) - self.total_venta
            if self.cambio_actual >= 0:
                self.lbl_cambio.configure(text=f"Cambio: $ {int(self.cambio_actual):,}".replace(",", "."),
                                          text_color=theme.COLORS["success"])
            else:
                self.lbl_cambio.configure(text="Falta dinero", text_color=theme.COLORS["danger"])
        except ValueError:
            self.lbl_cambio.configure(text="Inválido", text_color=theme.COLORS["danger"])

    def procesar(self):
        if not self.carrito: return
        mp = self.op_pago.get()
        ef_texto = self.ent_efectivo.get().replace(".", "").replace(",", "").replace("$", "").strip()
        ef = float(ef_texto or 0.0)

        if ef < self.total_venta: return messagebox.showerror("Error", "Pago insuficiente.")

        if messagebox.askyesno("Confirmar", f"¿Procesar venta por $ {int(self.total_venta):,}?"):
            exito, res = database.registrar_venta(self.carrito, self.total_venta, self.app.rol_actual, ef,
                                                  self.cambio_actual, mp)

            if exito:
                if self.chk_imprimir.get() == 1:
                    hardware.generar_ticket_impresion(res, self.carrito, self.total_venta, ef, self.cambio_actual, mp,
                                                      self.app.rol_actual)
                if mp == "Efectivo": hardware.abrir_cajon()

                self.carrito.clear()
                self.ent_efectivo.configure(state="normal")
                self.ent_efectivo.delete(0, 'end')
                self.actualizar_ui()
                self.app.actualizar_campana_alertas()
            else:
                messagebox.showerror("Error", res)

    def abrir_cierre_caja(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Arqueo y Cierre de Caja Diario")
        popup.geometry("920x720")
        popup.transient(self)
        popup.grab_set()

        top_f = ctk.CTkFrame(popup, fg_color="transparent")
        top_f.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(top_f, text="Generar informe para el día:", font=theme.FONTS["body_bold"]).pack(side="left",
                                                                                                     padx=10)
        cal = DateEntry(top_f, width=15, background=theme.COLORS["primary"], foreground='white', borderwidth=2,
                        date_pattern='y-mm-dd')
        cal.pack(side="left", padx=10)

        scroll = ctk.CTkScrollableFrame(popup, width=550, height=500, fg_color=theme.COLORS["bg_card"])
        scroll.pack(pady=10, padx=20, fill="both", expand=True)

        def generar_informe(e=None):
            for w in scroll.winfo_children(): w.destroy()
            fecha = cal.get()
            try:
                datos = database.generar_cierre_diario(fecha)
            except Exception as ex:
                return ctk.CTkLabel(scroll, text=f"Error: {ex}", text_color=theme.COLORS["danger"]).pack()

            def titulo(texto):
                ctk.CTkLabel(scroll, text=texto, font=theme.FONTS["h3"], text_color=theme.COLORS["primary"]).pack(
                    anchor="w", pady=(15, 5))

            def fila(clave, valor, color=theme.COLORS["text_main"], bold=False):
                f = ctk.CTkFrame(scroll, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=clave, font=theme.FONTS["body_bold"] if bold else theme.FONTS["body"],
                             text_color=color).pack(side="left")
                ctk.CTkLabel(f, text=valor, font=theme.FONTS["body_bold"] if bold else theme.FONTS["body"],
                             text_color=color).pack(side="right")

            titulo(f"RESUMEN DE INGRESOS - {fecha}")
            cajeros = datos.get('cajeros', [])
            fila("Cajeros en Turno:", ", ".join(cajeros) if cajeros else "Ninguno", theme.COLORS["text_muted"])
            fila("Efectivo en Caja Fuerte:", f"$ {int(datos.get('efectivo', 0)):,}".replace(",", "."),
                 theme.COLORS["success"])

            desglose_digital = datos.get('desglose_electronico', [])
            if desglose_digital:
                for metodo, monto in desglose_digital: fila(f"Pago vía {metodo}:",
                                                            f"$ {int(monto):,}".replace(",", "."),
                                                            theme.COLORS["success"])
            else:
                fila("Pagos Digitales:", "$ 0", theme.COLORS["success"])

            fila("TOTAL INGRESADO:", f"$ {int(datos.get('total_ingresos', 0)):,}".replace(",", "."),
                 theme.COLORS["success"], bold=True)

            titulo("VENTAS POR CATEGORÍA")
            categorias = datos.get('categorias', [])
            if categorias:
                for cat, total in categorias: fila(f"📦 {cat}:", f"$ {int(total):,}".replace(",", "."))
            else:
                ctk.CTkLabel(scroll, text="No hay ventas registradas este día.", text_color="gray").pack(anchor="w")

            titulo("SALIDAS DE DINERO (Gastos Físicos)")
            salidas = datos.get('salidas_detalle', [])
            if salidas:
                for cat, desc, monto in salidas: fila(f"💸 {cat} ({desc}):", f"- $ {int(monto):,}".replace(",", "."),
                                                      theme.COLORS["danger"])
                fila("TOTAL SALIDAS FÍSICAS:", f"- $ {int(datos.get('total_salidas', 0)):,}".replace(",", "."),
                     theme.COLORS["danger"], bold=True)
            else:
                ctk.CTkLabel(scroll, text="No hay salidas registradas este día.", text_color="gray").pack(anchor="w")

            titulo("ANÁLISIS DE RENTABILIDAD")
            fila("Reserva para Gastos Fijos (Prorrateo):",
                 f"- $ {int(datos.get('fijo_diario', 0)):,}".replace(",", "."), theme.COLORS["warning"])
            ganancia = datos.get('ganancia_neta', 0)
            color_ganancia = theme.COLORS["success"] if ganancia >= 0 else theme.COLORS["danger"]
            fila("GANANCIA NETA REAL DEL DÍA:", f"$ {int(ganancia):,}".replace(",", "."), color_ganancia, bold=True)

        cal.bind("<<DateEntrySelected>>", generar_informe)
        generar_informe()

    def abrir_historial(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Historial y Gestión de Ventas")
        popup.geometry("920x720")
        popup.transient(self)
        popup.grab_set()

        top_f = ctk.CTkFrame(popup, fg_color="transparent")
        top_f.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(top_f, text="Consultar Fecha:", font=theme.FONTS["body_bold"]).pack(side="left", padx=10)
        cal = DateEntry(top_f, width=15, background=theme.COLORS["primary"], foreground='white', borderwidth=2,
                        date_pattern='y-mm-dd')
        cal.pack(side="left", padx=10)

        tb_v = ttk.Treeview(popup, columns=("id", "hora", "cajero", "total", "pago"), show="headings", height=8)
        for c, t, w in [("id", "Factura #", 80), ("hora", "Hora", 100), ("cajero", "Cajero", 150),
                        ("total", "Total Venta", 120), ("pago", "Método Pago", 120)]:
            tb_v.heading(c, text=t)
            tb_v.column(c, width=w, anchor="center")
        tb_v.tag_configure('impar', background=theme.COLORS["table_odd"])
        tb_v.tag_configure('par', background=theme.COLORS["table_even"])
        tb_v.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(popup, text="Productos en esta factura:", font=theme.FONTS["body_bold"],
                     text_color=theme.COLORS["text_muted"]).pack(anchor="w", padx=20)
        tb_d = ttk.Treeview(popup, columns=("art", "cant", "subt"), show="headings", height=6)
        for c, t, w in [("art", "Artículo", 300), ("cant", "Cantidad", 80), ("subt", "Subtotal", 120)]:
            tb_d.heading(c, text=t)
            tb_d.column(c, width=w, anchor="center" if c != "art" else "w")
        tb_d.tag_configure('impar', background=theme.COLORS["table_odd"])
        tb_d.tag_configure('par', background=theme.COLORS["table_even"])
        tb_d.pack(pady=5, padx=20, fill="both", expand=True)

        def cargar_ventas(e=None):
            for r in tb_v.get_children(): tb_v.delete(r)
            for r in tb_d.get_children(): tb_d.delete(r)
            ventas = database.obtener_ventas_por_fecha(cal.get())
            for i, v in enumerate(ventas):
                hora = v[1].split()[1]
                tb_v.insert("", "end", values=(v[0], hora, v[2].upper(), f"$ {int(v[3]):,}", v[6]),
                            tags=('par',) if i % 2 == 0 else ('impar',))

        cal.bind("<<DateEntrySelected>>", cargar_ventas)
        cargar_ventas()

        def ver_detalles(e=None):
            for r in tb_d.get_children(): tb_d.delete(r)
            sel = tb_v.selection()
            if not sel: return
            vid = tb_v.item(sel[0])['values'][0]
            detalles = database.obtener_detalles_venta(vid)
            for i, d in enumerate(detalles):
                tb_d.insert("", "end", values=(d[1], f"{d[2]:g}", f"$ {int(d[4]):,}"),
                            tags=('par',) if i % 2 == 0 else ('impar',))

        tb_v.bind("<<TreeviewSelect>>", ver_detalles)

        bot_f = ctk.CTkFrame(popup, fg_color="transparent")
        bot_f.pack(pady=15, padx=20, fill="x")

        def reimprimir():
            sel = tb_v.selection()
            if not sel: return messagebox.showwarning("Aviso", "Seleccione una factura de la lista superior.")
            vid = tb_v.item(sel[0])['values'][0]
            v_info = database.obtener_venta_por_id(vid)
            detalles = database.obtener_detalles_venta(vid)
            carrito_recreado = [{'cantidad': d[2], 'nombre': d[1], 'precio': d[3], 'subtotal': d[4]} for d in detalles]
            hardware.generar_ticket_impresion(vid, carrito_recreado, v_info[3], v_info[4], v_info[5], v_info[6],
                                              v_info[2])
            messagebox.showinfo("Reimpresión", "Ticket enviado a la impresora térmica.")

        def anular():
            sel = tb_v.selection()
            if not sel: return messagebox.showwarning("Aviso", "Seleccione una factura de la lista superior.")
            if cal.get() != datetime.now().strftime('%Y-%m-%d'):
                return messagebox.showerror("Auditoría",
                                            "Por seguridad, solo se pueden anular ventas realizadas el día de hoy.")
            vid = tb_v.item(sel[0])['values'][0]
            if messagebox.askyesno("Anulación Contable",
                                   f"¿Está seguro de anular la Factura #{vid}?\n\nLos productos vendidos regresarán automáticamente al inventario y el dinero se restará de la caja."):
                exito, msg = database.anular_venta(vid)
                if exito:
                    messagebox.showinfo("Éxito", msg)
                    cargar_ventas()
                    self.app.actualizar_campana_alertas()
                else:
                    messagebox.showerror("Error de Base de Datos", msg)

        ctk.CTkButton(bot_f, text="🖨️ Reimprimir Ticket", height=40, font=theme.FONTS["body_bold"],
                      fg_color=theme.COLORS["primary"], command=reimprimir).pack(side="left", padx=10)
        ctk.CTkButton(bot_f, text="🗑️ Anular Venta (Devolver Stock)", height=40, font=theme.FONTS["body_bold"],
                      fg_color=theme.COLORS["danger"], command=anular).pack(side="right", padx=10)

    def abrir_buscador(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Búsqueda Avanzada")
        popup.geometry("840x720")
        popup.transient(self)
        popup.grab_set()

        sf = ctk.CTkFrame(popup, fg_color="transparent")
        sf.pack(pady=10, padx=20, fill="x")
        ent_n = ctk.CTkEntry(sf, placeholder_text="Escriba el nombre del producto...", width=400, height=40)
        ent_n.pack(side="left", padx=10)

        tb = ttk.Treeview(popup, columns=("codigo", "nombre", "precio", "stock"), show="headings", height=10)
        for c, t, w in [("codigo", "Código", 100), ("nombre", "Nombre", 300), ("precio", "Precio", 100),
                        ("stock", "Stock", 80)]:
            tb.heading(c, text=t)
            tb.column(c, width=w)
        tb.tag_configure('impar', background=theme.COLORS["table_odd"])
        tb.tag_configure('par', background=theme.COLORS["table_even"])
        tb.pack(pady=10, padx=20, fill="both", expand=True)

        def refrescar(e=None):
            for row in tb.get_children(): tb.delete(row)
            for i, p in enumerate(database.buscar_productos("", ent_n.get())):
                tb.insert("", "end", values=(p[0], p[1], f"$ {int(p[4]):,}", f"{p[5]:g}"),
                          tags=('par',) if i % 2 == 0 else ('impar',))

        ent_n.bind("<KeyRelease>", refrescar)
        refrescar()

        def seleccionar(e=None):
            sel = tb.selection()
            if sel:
                self.ent_codigo.delete(0, 'end')
                self.ent_codigo.insert(0, str(tb.item(sel[0])['values'][0]))
                self.add_carrito()
                popup.destroy()

        tb.bind("<Double-1>", seleccionar)
        ctk.CTkButton(popup, text="Añadir a Factura", height=40, fg_color=theme.COLORS["success"],
                      font=theme.FONTS["body_bold"], command=seleccionar).pack(pady=15)


# (Resto de Vistas: InventarioView, FinanzasView, etc. permanecen intactas en tu código original, pégalas aquí debajo)
# ...
# ==========================================
# 3. INVENTARIO
# ==========================================
class InventarioView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        ctk.CTkLabel(self, text="Inventario de Productos", font=theme.FONTS["h1"]).pack(pady=(20, 10))

        sf = ctk.CTkFrame(self, fg_color="transparent"); sf.pack(pady=(0, 10), padx=20, fill="x")
        self.e_cod = ctk.CTkEntry(sf, placeholder_text="🔍 Código...", width=150, height=35)
        self.e_cod.pack(side="left", padx=(0, 10)); self.e_cod.bind("<KeyRelease>", self.actualizar_tabla)
        
        self.e_nom = ctk.CTkEntry(sf, placeholder_text="🔍 Nombre...", width=200, height=35)
        self.e_nom.pack(side="left"); self.e_nom.bind("<KeyRelease>", self.actualizar_tabla)
        
        ctk.CTkButton(sf, text="🗑️ Eliminar", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["danger"], hover_color=theme.COLORS["danger_hover"], width=100, command=self.eliminar).pack(side="right", padx=(10, 0))
        ctk.CTkButton(sf, text="✏️ Modificar", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["warning"], hover_color=theme.COLORS["warning_hover"], width=100, command=self.editar).pack(side="right")

        tf = ctk.CTkFrame(self, fg_color="transparent"); tf.pack(pady=10, padx=20, fill="both", expand=True)
        self.tabla = ttk.Treeview(tf, columns=("cod", "nom", "cat", "ven", "stk", "f_cad"), show="headings", height=15)
        for c, t, w in [("cod","Código",100),("nom","Producto",200),("cat","Categoría",120),("ven","Venta (Normal)",120),("stk","Stock",80),("f_cad","Caducidad",120)]:
            self.tabla.heading(c, text=t); self.tabla.column(c, width=w, anchor="center" if c!="nom" else "w")
            
        self.tabla.tag_configure('impar', background=theme.COLORS["table_odd"])
        self.tabla.tag_configure('par', background=theme.COLORS["table_even"])
        self.tabla.tag_configure('peligro', background=theme.COLORS["table_danger"], foreground='white') 
        self.tabla.pack(side="left", fill="both", expand=True)
        
        scrollbar = ctk.CTkScrollbar(tf, orientation="vertical", command=self.tabla.yview)
        scrollbar.pack(side="right", fill="y", padx=(5, 0)); self.tabla.configure(yscrollcommand=scrollbar.set)
        self.actualizar_tabla()

    def actualizar_tabla(self, e=None):
        for row in self.tabla.get_children(): self.tabla.delete(row)
        for i, p in enumerate(database.buscar_productos(self.e_cod.get(), self.e_nom.get())):
            frac_icon = " ⚖️" if p[8] == 1 else ""
            caducidad = p[7] if p[7] else "N/A"
            fila = (p[0], f"{p[1]}{frac_icon}", str(p[2]), f"$ {int(p[4]):,}", f"{p[5]:g}", caducidad)
            
            # EL BLINDAJE: Usamos iid=str(p[0]) para guardar el código original como una etiqueta inmodificable
            self.tabla.insert("", "end", iid=str(p[0]), values=fila, tags=('peligro',) if p[5] <= p[6] else (('par',) if i % 2 == 0 else ('impar',)))
        self.app.actualizar_campana_alertas() 

    def editar(self):
        sel = self.tabla.selection()
        if sel:
            # Ahora leemos el 'iid' directamente, garantizando que tenemos el código 100% real
            codigo = sel[0] 
            producto_real = database.buscar_producto_exacto(codigo)
            if producto_real:
                self.app.cambiar_vista(FormularioProductoView, editar_datos=producto_real)
            else:
                messagebox.showerror("Error", f"No se pudo cargar el código: {codigo}")

    def eliminar(self):
        sel = self.tabla.selection()
        if sel:
            codigo = sel[0] # Código real garantizado
            nombre = self.tabla.item(sel[0])['values'][1]
            if messagebox.askyesno("Borrar", f"¿Eliminar {nombre}?"):
                database.eliminar_producto(codigo)
                self.actualizar_tabla()


# ==========================================
# 4. FORMULARIO DE PRODUCTO (Versión Final Corregida)
# ==========================================
# ==========================================
# 4. FORMULARIO DE PRODUCTO (Versión Final Corregida)
# ==========================================
class FormularioProductoView(ViewBase):
    def __init__(self, master, app, editar_datos=None):
        super().__init__(master, app)
        ctk.CTkLabel(self, text="Ficha Técnica del Producto", font=theme.FONTS["h1"]).pack(pady=(15, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color=theme.COLORS["bg_card"])
        scroll.pack(pady=10, padx=30, fill="both", expand=True)

        def seccion(texto):
            ctk.CTkLabel(scroll, text=texto, font=theme.FONTS["h3"], text_color=theme.COLORS["primary"]).pack(
                anchor="w", padx=20, pady=(20, 5))

        def crear_campo(padre, texto, placeholder, ancho):
            f = ctk.CTkFrame(padre, fg_color="transparent")
            f.pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(f, text=texto, font=theme.FONTS["body_bold"]).pack(anchor="w")
            e = ctk.CTkEntry(f, placeholder_text=placeholder, width=ancho, height=35)
            e.pack()
            return e

        # --- 1. INFO BÁSICA ---
        seccion("1. Información Básica")
        f1 = ctk.CTkFrame(scroll, fg_color="transparent")
        f1.pack(fill="x", padx=10)
        self.e_cod = crear_campo(f1, "Código de Barras *", "Ej: 77012345", 180)
        self.e_nom = crear_campo(f1, "Nombre del Producto *", "Ej: Aceite 4T", 250)

        f_cat = ctk.CTkFrame(f1, fg_color="transparent")
        f_cat.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(f_cat, text="Categoría *", font=theme.FONTS["body_bold"]).pack(anchor="w")
        cats = database.obtener_categorias()
        self.e_cat = ctk.CTkComboBox(f_cat, values=cats if cats else ["General"], width=150, height=35)
        self.e_cat.pack()

        # --- 2. PRECIOS BASE ---
        seccion("2. Costos y Precio Base")
        f2 = ctk.CTkFrame(scroll, fg_color="transparent")
        f2.pack(fill="x", padx=10)
        self.e_cos = crear_campo(f2, "Costo Compra ($)", "0", 150)
        self.e_ven = crear_campo(f2, "Precio Venta Normal ($)", "0", 150)

        # --- 3. VENTAS ESPECIALES ---
        seccion("3. Modalidades de Venta Especial (Opcional)")
        f3 = ctk.CTkFrame(scroll, fg_color="transparent")
        f3.pack(fill="x", padx=10)

        box_may = ctk.CTkFrame(f3, fg_color=theme.COLORS["bg_panel"], corner_radius=8)
        box_may.pack(side="left", padx=10, fill="y", ipadx=10, ipady=10)
        ctk.CTkLabel(box_may, text="📦 Descuento por Mayoreo", font=theme.FONTS["body_bold"],
                     text_color=theme.COLORS["warning"]).pack(anchor="w", padx=10)
        row_m = ctk.CTkFrame(box_may, fg_color="transparent")
        row_m.pack()
        self.e_cant_may = crear_campo(row_m, "A partir de (Cant):", "0", 160)
        self.e_pre_may = crear_campo(row_m, "Precio Unit. ($):", "0", 160)

        box_frac = ctk.CTkFrame(f3, fg_color=theme.COLORS["bg_panel"], corner_radius=8)
        box_frac.pack(side="left", padx=10, fill="y", ipadx=10, ipady=10)
        self.chk_fraccion = ctk.CTkSwitch(box_frac, text="🧩 Vende por Fracción", font=theme.FONTS["body_bold"])
        self.chk_fraccion.pack(anchor="w", padx=10, pady=(5, 0))
        row_f = ctk.CTkFrame(box_frac, fg_color="transparent")
        row_f.pack()
        self.e_pre_frac = crear_campo(row_f, "Precio Fracción ($):", "0", 180)
        self.e_div_frac = crear_campo(row_f, "Partes por Entero (Ej: 8):", "1", 180)

        # --- 4. INVENTARIO ---
        seccion("4. Inventario y Trazabilidad")
        f4 = ctk.CTkFrame(scroll, fg_color="transparent")
        f4.pack(fill="x", padx=10)
        self.e_stk = crear_campo(f4, "Stock Actual", "0", 120)
        self.e_min = crear_campo(f4, "Alarma Mínima", "5", 120)
        self.e_cad = crear_campo(f4, "Fecha Caducidad", "AAAA-MM-DD", 160)

        self.lbl_msg = ctk.CTkLabel(scroll, text="", font=theme.FONTS["body_bold"])
        self.lbl_msg.pack(pady=15)

        # --- LÓGICA DE CARGA DE DATOS Y BOTÓN FINAL ---
        if editar_datos:
            def seguro(valor):
                if valor is None or valor == "": return "0"
                return f"{valor:g}" if isinstance(valor, (int, float)) else str(valor)

            self.e_cod.insert(0, editar_datos[0])
            self.e_cod.configure(state="disabled")
            self.e_nom.insert(0, editar_datos[1] or "")
            self.e_ven.insert(0, seguro(editar_datos[2]))
            self.e_stk.insert(0, seguro(editar_datos[3]))
            self.e_cos.insert(0, seguro(editar_datos[4]))
            self.e_cat.set(editar_datos[5] or "General")

            if editar_datos[6] == 1: self.chk_fraccion.select()

            self.e_pre_may.insert(0, seguro(editar_datos[7]))
            self.e_cant_may.insert(0, seguro(editar_datos[8]))
            self.e_pre_frac.insert(0, seguro(editar_datos[9]))

            if editar_datos[10]: self.e_cad.insert(0, str(editar_datos[10]))

            val_div = editar_datos[11] if len(editar_datos) > 11 else 1
            self.e_div_frac.insert(0, seguro(val_div))

            self.btn_accion = ctk.CTkButton(scroll, text="Actualizar Ficha Técnica", font=theme.FONTS["body_bold"],
                                            fg_color=theme.COLORS["warning"], hover_color=theme.COLORS["warning_hover"],
                                            height=45, command=self.guardar)
            self.btn_accion.pack(pady=25)
        else:
            self.e_cat.set("General")
            self.e_min.insert(0, "5")
            self.e_pre_may.insert(0, "")
            self.e_cant_may.insert(0, "")
            self.e_pre_frac.insert(0, "")
            self.e_cos.insert(0, "")
            self.e_ven.insert(0, "")
            self.e_stk.insert(0, "")
            self.e_div_frac.insert(0, "1")

            self.btn_accion = ctk.CTkButton(scroll, text="Guardar Nuevo Producto", font=theme.FONTS["body_bold"],
                                            fg_color=theme.COLORS["success"], hover_color=theme.COLORS["success_hover"],
                                            height=45, command=self.guardar)
            self.btn_accion.pack(pady=25)

    def guardar(self):
        c, n, cat = self.e_cod.get().strip(), self.e_nom.get().upper().strip(), self.e_cat.get().title().strip()
        f_cad = self.e_cad.get().strip()
        es_frac = 1 if self.chk_fraccion.get() == 1 else 0

        if not c or not n or not cat: return self.lbl_msg.configure(text="Faltan datos obligatorios.",
                                                                    text_color=theme.COLORS["danger"])
        try:
            cos = float(self.e_cos.get().replace(",", ".") or 0)
            ven = float(self.e_ven.get().replace(",", ".") or 0)
            stk = float(self.e_stk.get().replace(",", ".") or 0)
            mnm = float(self.e_min.get().replace(",", ".") or 5)
            p_may = float(self.e_pre_may.get().replace(",", ".") or 0)
            c_may = float(self.e_cant_may.get().replace(",", ".") or 0)
            p_frac = float(self.e_pre_frac.get().replace(",", ".") or 0)
            div_frac = float(self.e_div_frac.get().replace(",", ".") or 1)

            if div_frac <= 0: div_frac = 1.0

            if cos < 0 or ven < 0: return self.lbl_msg.configure(text="Precios no pueden ser negativos.",
                                                                 text_color=theme.COLORS["danger"])

            if self.e_cod.cget("state") == "disabled":
                exito, msg = database.actualizar_producto(c, n, cat, cos, ven, stk, mnm, es_frac, p_may, c_may, p_frac,
                                                          f_cad, div_frac)
            else:
                exito, msg = database.agregar_producto(c, n, cat, cos, ven, stk, mnm, es_frac, p_may, c_may, p_frac,
                                                       f_cad, div_frac)

            if exito:
                self.lbl_msg.configure(text=msg, text_color=theme.COLORS["success"])
                if self.e_cod.cget("state") != "disabled":
                    for e in [self.e_cod, self.e_nom, self.e_cos, self.e_ven, self.e_stk, self.e_pre_may,
                              self.e_cant_may, self.e_pre_frac, self.e_div_frac, self.e_cad]: e.delete(0, 'end')
                self.app.actualizar_campana_alertas()
            else:
                self.lbl_msg.configure(text=msg, text_color=theme.COLORS["danger"])
        except ValueError:
            self.lbl_msg.configure(text="Error numérico.", text_color=theme.COLORS["danger"])

# ==========================================
# 5. FINANZAS Y GASTOS 
# ==========================================
class FinanzasView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        ctk.CTkLabel(self, text="Inteligencia de Negocios (BI)", font=theme.FONTS["h1"]).pack(pady=(20, 10))
        tv = ctk.CTkTabview(self, width=900, height=600, fg_color=theme.COLORS["bg_card"]); tv.pack(padx=20, pady=10, fill="both", expand=True)
        tab_rep = tv.add("📊 Dashboard y Flujo de Caja")
        tab_gas = tv.add("💸 Control de Gastos")

        self.init_dashboard(tab_rep)
        self.init_gastos(tab_gas)

    def init_dashboard(self, tab):
        tab.grid_columnconfigure(0, weight=0); tab.grid_columnconfigure(1, weight=1); tab.grid_rowconfigure(0, weight=1)
        ff = ctk.CTkFrame(tab, width=280, corner_radius=10, fg_color=theme.COLORS["bg_panel"]); ff.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); ff.grid_propagate(False)

        ctk.CTkLabel(ff, text="Rango", font=theme.FONTS["h3"]).pack(pady=(20, 10))
        qf = ctk.CTkFrame(ff, fg_color="transparent"); qf.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(qf, text="Hoy", width=70, font=theme.FONTS["body"], command=lambda: self.set_f(0)).pack(side="left", padx=2)
        ctk.CTkButton(qf, text="Sem.", width=70, font=theme.FONTS["body"], command=lambda: self.set_f(7)).pack(side="left", padx=2)
        ctk.CTkButton(qf, text="Mes", width=70, font=theme.FONTS["body"], command=lambda: self.set_f(30)).pack(side="left", padx=2)

        self.f_ini = DateEntry(ff, width=15, background=theme.COLORS["primary"], foreground='white', borderwidth=2, date_pattern='y-mm-dd'); self.f_ini.pack(pady=(10,5), padx=20, fill="x")
        self.f_fin = DateEntry(ff, width=15, background=theme.COLORS["primary"], foreground='white', borderwidth=2, date_pattern='y-mm-dd'); self.f_fin.pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(ff, text="Generar", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["primary"], command=self.actualizar_dash).pack(pady=(15, 20), padx=20)

        self.cards_f = ctk.CTkFrame(tab, fg_color="transparent"); self.cards_f.grid(row=0, column=1, padx=10, pady=10, sticky="nw")
        self.chart_f = ctk.CTkFrame(tab, fg_color=theme.COLORS["bg_main"], corner_radius=10); self.chart_f.grid(row=0, column=1, padx=10, pady=(130, 10), sticky="nsew")
        self.actualizar_dash()

    def set_f(self, d):
        hoy = datetime.now(); self.f_fin.set_date(hoy)
        if d==0: self.f_ini.set_date(hoy)
        elif d==7: self.f_ini.set_date(hoy - timedelta(days=hoy.weekday()))
        elif d==30: self.f_ini.set_date(hoy.replace(day=1))
        self.actualizar_dash()

    def actualizar_dash(self):
        for w in self.cards_f.winfo_children(): w.destroy()
        for w in self.chart_f.winfo_children(): w.destroy()

        ini, fin = self.f_ini.get(), self.f_fin.get()
        d = database.generar_reporte_financiero(ini, fin)

        col_idx = 0
        def add_c(tit, val, col):
            nonlocal col_idx
            c = ctk.CTkFrame(self.cards_f, fg_color=col, corner_radius=10, width=180, height=90); c.grid(row=0, column=col_idx, padx=10); c.grid_propagate(False) 
            ctk.CTkLabel(c, text=tit, font=theme.FONTS["table_header"], text_color="#FFF").pack(pady=(10, 0)); ctk.CTkLabel(c, text=f"$ {int(val):,}".replace(",", "."), font=theme.FONTS["h3"], text_color="#FFF").pack(pady=5)
            col_idx += 1

        add_c("Ingresos", d['ventas_totales'], theme.COLORS["primary"]); add_c("Mercancía", d['costo_mercancia'], theme.COLORS["warning"])
        add_c("Gastos", d['gastos_operativos'], theme.COLORS["special"]); add_c("Efectivo", d['efectivo_caja'], theme.COLORS["bg_input"])
        add_c("Ganancia Neta", d['ganancia_neta'], theme.COLORS["success"] if d['ganancia_neta']>=0 else theme.COLORS["danger"])

        fig, ax = plt.subplots(figsize=(6, 3), facecolor=theme.COLORS["bg_main"]); ax.set_facecolor(theme.COLORS["bg_main"]); ax.tick_params(colors='white'); ax.spines['bottom'].set_color('white'); ax.spines['left'].set_color('white'); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.bar(["Ingreso", "Costo", "Gasto", "Ganancia"], [d['ventas_totales'], d['costo_mercancia'], d['gastos_operativos'], d['ganancia_neta']], color=[theme.COLORS["primary"], theme.COLORS["warning"], theme.COLORS["special"], theme.COLORS["success"]], width=0.5)
        plt.tight_layout()
        FigureCanvasTkAgg(fig, master=self.chart_f).draw(); FigureCanvasTkAgg(fig, master=self.chart_f).get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10); plt.close(fig)

    def init_gastos(self, tab):
        ff = ctk.CTkFrame(tab, fg_color=theme.COLORS["bg_card"]); ff.pack(pady=15, padx=20, fill="x")
        self.o_cat = ctk.CTkOptionMenu(ff, values=["Arriendo", "Servicios", "Nómina", "Insumos", "Otros"]); self.o_cat.pack(side="left", padx=10, pady=15)
        self.o_frec = ctk.CTkOptionMenu(ff, values=["Mensual", "Diario"], width=100); self.o_frec.pack(side="left", padx=5)
        self.e_des = ctk.CTkEntry(ff, placeholder_text="Descripción..."); self.e_des.pack(side="left", padx=10)
        self.e_mon = ctk.CTkEntry(ff, placeholder_text="Monto ($)", width=120); self.e_mon.pack(side="left", padx=10)
        ctk.CTkButton(ff, text="Registrar", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["danger"], command=self.guardar_gas).pack(side="right", padx=20)

        tf = ctk.CTkFrame(tab, fg_color="transparent"); tf.pack(fill="both", expand=True, padx=20, pady=10)
        self.t_gas = ttk.Treeview(tf, columns=("fec", "cat", "fre", "des", "mon", "usr"), show="headings", height=10)
        for c, t, w in [("fec","Fecha",120),("cat","Categoría",120),("fre","Frecuencia",100),("des","Descripción",200),("mon","Monto",100),("usr","Cajero",100)]: 
            self.t_gas.heading(c, text=t); self.t_gas.column(c, width=w, anchor="center")
        self.t_gas.tag_configure('impar', background=theme.COLORS["table_odd"]); self.t_gas.tag_configure('par', background=theme.COLORS["table_even"]); self.t_gas.pack(side="left", fill="both", expand=True)
        self.act_gas()

    def guardar_gas(self):
        try:
            database.registrar_gasto(self.o_cat.get(), self.o_frec.get(), self.e_des.get(), float(self.e_mon.get()), self.app.rol_actual)
            self.e_des.delete(0, 'end'); self.e_mon.delete(0, 'end'); self.act_gas(); self.actualizar_dash()
        except: messagebox.showerror("Error", "Datos inválidos.")

    def act_gas(self):
        for r in self.t_gas.get_children(): self.t_gas.delete(r)
        hoy = datetime.now().strftime('%Y-%m-%d')
        for i, g in enumerate(database.obtener_gastos(hoy, hoy)): 
            self.t_gas.insert("", "end", values=(g[0], g[1], g[2], g[3], f"$ {int(g[4]):,}", g[5]), tags=('par',) if i%2==0 else ('impar',))

# ==========================================
# 6. AJUSTES
# ==========================================
class AjustesView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        ctk.CTkLabel(self, text="Configuración del Recibo", font=theme.FONTS["h1"]).pack(pady=(20, 30))
        ff = ctk.CTkFrame(self, width=500, fg_color=theme.COLORS["bg_card"]); ff.pack(pady=10, padx=50, fill="y", expand=True)
        c = database.obtener_configuracion()
        def campo(txt, key):
            ctk.CTkLabel(ff, text=txt, font=theme.FONTS["body_bold"]).pack(pady=(15, 0), anchor="w", padx=40)
            e = ctk.CTkEntry(ff, width=400, height=40); e.insert(0, c.get(key, "")); e.pack(pady=(5, 10), padx=40); return e
        self.c1 = campo("Nombre Empresa:", "empresa"); self.c2 = campo("NIT:", "nit"); self.c3 = campo("Dirección:", "direccion"); self.c4 = campo("Teléfono:", "telefono"); self.c5 = campo("Mensaje Final:", "mensaje")
        ctk.CTkButton(ff, text="💾 Guardar Cambios", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["success"], hover_color=theme.COLORS["success_hover"], height=45, command=self.guardar).pack(pady=30)

    def guardar(self):
        exito, m = database.actualizar_configuracion(self.c1.get().strip().upper(), self.c2.get(), self.c3.get(), self.c4.get(), self.c5.get())
        if exito: messagebox.showinfo("Guardado", m)
        else: messagebox.showerror("Error", m)

# ==========================================
# 7. USUARIOS
# ==========================================
class UsuariosView(ViewBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        ctk.CTkLabel(self, text="Gestión de Personal", font=theme.FONTS["h1"]).pack(pady=(20, 10))
        form_frame = ctk.CTkFrame(self, fg_color=theme.COLORS["bg_card"]); form_frame.pack(pady=10, padx=20, fill="x")
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent"); row1.pack(pady=5, fill="x", padx=10)
        self.reg_nombre = ctk.CTkEntry(row1, placeholder_text="Nombre Completo", width=250); self.reg_nombre.pack(side="left", padx=5)
        self.reg_doc = ctk.CTkEntry(row1, placeholder_text="Documento", width=160); self.reg_doc.pack(side="left", padx=5)
        self.reg_tel = ctk.CTkEntry(row1, placeholder_text="Teléfono", width=130); self.reg_tel.pack(side="left", padx=5)
        self.reg_correo = ctk.CTkEntry(row1, placeholder_text="Correo Electrónico", width=200); self.reg_correo.pack(side="left", padx=5)
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent"); row2.pack(pady=10, fill="x", padx=10)
        self.reg_user = ctk.CTkEntry(row2, placeholder_text="Nuevo Usuario", width=180); self.reg_user.pack(side="left", padx=5)
        self.reg_pass = ctk.CTkEntry(row2, placeholder_text="Contraseña", width=150, show="*"); self.reg_pass.pack(side="left", padx=5)
        ctk.CTkLabel(row2, text="Rol:", font=theme.FONTS["body_bold"]).pack(side="left", padx=(10, 2))
        self.reg_rol = ctk.CTkOptionMenu(row2, values=["cajero", "admin"], width=100); self.reg_rol.pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Crear Perfil", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["success"], hover_color=theme.COLORS["success_hover"], command=self.procesar_crear_usuario).pack(side="right", padx=10)
        ctk.CTkButton(self, text="🗑️ Eliminar Usuario", font=theme.FONTS["body_bold"], fg_color=theme.COLORS["danger"], hover_color=theme.COLORS["danger_hover"], command=self.procesar_eliminar_usuario).pack(pady=5, padx=20, anchor="e")
        table_frame = ctk.CTkFrame(self, fg_color="transparent"); table_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.tabla_usr = ttk.Treeview(table_frame, columns=("user", "rol", "nombre", "doc", "tel"), show="headings", height=10)
        for c, t, w in [("user","Usuario",120), ("rol","Rol",80), ("nombre","Nombre",250), ("doc","Documento",120), ("tel","Teléfono",120)]:
            self.tabla_usr.heading(c, text=t); self.tabla_usr.column(c, width=w, anchor="center" if c!="nombre" else "w")
        self.tabla_usr.tag_configure('impar', background=theme.COLORS["table_odd"]); self.tabla_usr.tag_configure('par', background=theme.COLORS["table_even"]); self.tabla_usr.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tabla_usr.yview); scrollbar.pack(side="right", fill="y", padx=(5, 0)); self.tabla_usr.configure(yscrollcommand=scrollbar.set)
        self.actualizar_tabla_usuarios()

    def actualizar_tabla_usuarios(self):
        for row in self.tabla_usr.get_children(): self.tabla_usr.delete(row)
        for index, u in enumerate(database.obtener_usuarios()):
            self.tabla_usr.insert("", "end", values=(u[0], u[1].upper(), u[2] or "N/A", u[3] or "N/A", u[4] or "N/A"), tags=('par',) if index % 2 == 0 else ('impar',))

    def procesar_crear_usuario(self):
        if not self.reg_user.get() or not self.reg_pass.get() or not self.reg_nombre.get(): return messagebox.showerror("Error", "Usuario, contraseña y nombre son obligatorios.")
        exito, msg = database.crear_usuario(self.reg_user.get(), self.reg_pass.get(), self.reg_rol.get(), self.reg_nombre.get(), self.reg_doc.get(), self.reg_tel.get(), self.reg_correo.get())
        if exito:
            for e in [self.reg_nombre, self.reg_doc, self.reg_tel, self.reg_correo, self.reg_user, self.reg_pass]: e.delete(0, 'end')
            self.actualizar_tabla_usuarios(); messagebox.showinfo("Éxito", msg)
        else: messagebox.showerror("Error", msg)

    def procesar_eliminar_usuario(self):
        sel = self.tabla_usr.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione un usuario.")
        user = self.tabla_usr.item(sel)['values'][0]
        if messagebox.askyesno("Borrar", f"¿Eliminar al usuario {user}?"):
            exito, msg = database.eliminar_usuario(user)
            if exito: self.actualizar_tabla_usuarios()
            else: messagebox.showerror("Error", msg)