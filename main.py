import customtkinter as ctk
from tkinter import ttk, messagebox
import theme
import database
import views # Importamos nuestras pantallas modulares

database.inicializar_bd()
ctk.set_appearance_mode("Dark")

class KuroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kuro Systems - Acceso Restringido")
        self.geometry("1250x800")
        self.minsize(1050, 700)
        self.rol_actual = None
        self.current_view = None

        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.aplicar_estilos_globales()
        self.mostrar_login()

    def aplicar_estilos_globales(self):
        style = ttk.Style(); style.theme_use("default")
        style.configure("Treeview", background=theme.COLORS["table_odd"], foreground=theme.COLORS["text_main"], rowheight=35, fieldbackground=theme.COLORS["bg_main"], borderwidth=0, font=theme.FONTS["table"])
        style.map('Treeview', background=[('selected', theme.COLORS["table_selected"])])
        style.configure("Treeview.Heading", background=theme.COLORS["table_header"], foreground=theme.COLORS["text_main"], font=theme.FONTS["table_header"], borderwidth=0, padding=5)
        style.map("Treeview.Heading", background=[('active', theme.COLORS["table_selected"])])

    def limpiar_todo(self):
        for widget in self.winfo_children(): widget.destroy()

    def mostrar_login(self):
        self.limpiar_todo()
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=0)
        self.current_view = views.LoginView(self, self) # Instanciamos el componente Login

    def procesar_login(self, user, password):
        exito, rol = database.verificar_login(user, password)
        if exito:
            self.rol_actual = rol; self.title(f"Kuro Systems - Usuario: {user.upper()} | Rol: {rol.upper()}")
            self.construir_interfaz_principal()
            return True
        return False

    def construir_interfaz_principal(self):
        self.limpiar_todo()
        self.grid_columnconfigure(0, weight=0); self.grid_columnconfigure(1, weight=1)

        # --- BARRA LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=theme.COLORS["bg_panel"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="KURO\nSYSTEMS", font=theme.FONTS["h2"], text_color=theme.COLORS["text_main"]).pack(pady=(20, 20), padx=20)

        # Botón Alertas (Añadido fill="x" y height=40)
        self.btn_alertas = ctk.CTkButton(self.sidebar, text="🔔 Alertas", font=theme.FONTS["body_bold"], height=40, command=self.mostrar_alertas)
        self.btn_alertas.pack(pady=(0, 20), padx=20, fill="x")

        # Enrutador Dinámico (Dependiendo del rol)
        if self.rol_actual == "admin":
            self.crear_btn("📊 Inteligencia Financiera", theme.COLORS["special"], theme.COLORS["special_hover"], views.FinanzasView)
            self.crear_btn("📋 Inventario de Stock", theme.COLORS["primary"], theme.COLORS["primary_hover"], views.InventarioView)
            self.crear_btn("➕ Ingresar Producto", theme.COLORS["primary"], theme.COLORS["primary_hover"], views.FormularioProductoView)
            self.crear_btn("👥 Gestión Personal", theme.COLORS["bg_input"], theme.COLORS["bg_input"], views.UsuariosView)
            self.crear_btn("⚙️ Ajustes de Tienda", theme.COLORS["bg_input"], theme.COLORS["bg_input"], views.AjustesView)

        self.crear_btn("🧾 Terminal de Cobro", theme.COLORS["primary"], theme.COLORS["primary_hover"], views.POSView)

        # Botón Cerrar Sesión (Añadido fill="x" y height=40)
        ctk.CTkButton(self.sidebar, text="🚪 Cerrar Sesión", font=theme.FONTS["body_bold"], height=40, fg_color=theme.COLORS["danger"], hover_color=theme.COLORS["danger_hover"], command=self.mostrar_login).pack(pady=(50, 10), padx=20, fill="x", side="bottom")

        # --- ÁREA CENTRAL ---
        self.main_container = ctk.CTkFrame(self, corner_radius=10, fg_color=theme.COLORS["bg_main"])
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.actualizar_campana_alertas()
        if self.rol_actual == "admin": self.cambiar_vista(views.FinanzasView)
        else: self.cambiar_vista(views.POSView)

    def crear_btn(self, texto, color, hover, view_class):
        # AÑADIDO: height=40 (altura uniforme), anchor="w" (texto a la izquierda) y fill="x" (estirar a lo ancho)
        ctk.CTkButton(self.sidebar, text=texto, font=theme.FONTS["body"], height=40, anchor="w", fg_color=color, hover_color=hover, command=lambda: self.cambiar_vista(view_class)).pack(pady=10, padx=20, fill="x")
    # MOTOR DE ENRUTAMIENTO: Destruye la pantalla vieja y dibuja la nueva
    def cambiar_vista(self, view_class, **kwargs):
        if self.current_view: self.current_view.destroy()
        self.current_view = view_class(self.main_container, self, **kwargs)

    def actualizar_campana_alertas(self):
        alertas_stk = database.obtener_alertas_stock()
        alertas_cad = database.obtener_alertas_caducidad()
        total = len(alertas_stk) + len(alertas_cad)

        if total > 0:
            self.btn_alertas.configure(text=f"🔔 Alertas ({total})", fg_color=theme.COLORS["danger"], hover_color=theme.COLORS["danger_hover"])
        else:
            self.btn_alertas.configure(text="🔔 Alertas (0)", fg_color=theme.COLORS["success"], hover_color=theme.COLORS["success_hover"])

    def mostrar_alertas(self):
        alertas_stk = database.obtener_alertas_stock()
        alertas_cad = database.obtener_alertas_caducidad()

        popup = ctk.CTkToplevel(self)
        popup.title("Centro de Alertas de Inventario")
        popup.geometry("600x550")
        popup.transient(self)
        popup.grab_set()

        # Pestañas para no mezclar stock con caducidad
        tv = ctk.CTkTabview(popup)
        tv.pack(fill="both", expand=True, padx=20, pady=20)
        t_stk = tv.add(f"⚠️ Stock Crítico ({len(alertas_stk)})")
        t_cad = tv.add(f"⏳ Caducidad ({len(alertas_cad)})")

        # --- TAB DE STOCK ---
        scroll_stk = ctk.CTkScrollableFrame(t_stk, fg_color="transparent")
        scroll_stk.pack(fill="both", expand=True)
        if not alertas_stk:
            ctk.CTkLabel(scroll_stk, text="Todos los productos tienen niveles óptimos.", text_color=theme.COLORS["success"]).pack(pady=50)
        else:
            for p in alertas_stk:
                box = ctk.CTkFrame(scroll_stk, fg_color=theme.COLORS["table_danger"], corner_radius=5); box.pack(pady=5, fill="x")
                ctk.CTkLabel(box, text=f"[{p[0]}] {p[1]}\nStock Actual: {p[2]} (Mínimo: {p[3]})", text_color=theme.COLORS["text_main"], justify="left").pack(padx=10, pady=10, anchor="w")

        # --- TAB DE CADUCIDAD ---
        scroll_cad = ctk.CTkScrollableFrame(t_cad, fg_color="transparent")
        scroll_cad.pack(fill="both", expand=True)
        if not alertas_cad:
            ctk.CTkLabel(scroll_cad, text="No hay productos próximos a vencer en los próximos 30 días.", text_color=theme.COLORS["success"]).pack(pady=50)
        else:
            for cod, nom, fecha, estado in alertas_cad:
                color_box = theme.COLORS["danger"] if "VENCIDO" in estado or "HOY" in estado else theme.COLORS["warning"]
                box = ctk.CTkFrame(scroll_cad, fg_color=color_box, corner_radius=5); box.pack(pady=5, fill="x")
                ctk.CTkLabel(box, text=f"[{cod}] {nom}\nFecha registrada: {fecha}  ➔  {estado}", text_color=theme.COLORS["text_main"], justify="left").pack(padx=10, pady=10, anchor="w")


if __name__ == "__main__":
    app = KuroApp()
    app.mainloop()