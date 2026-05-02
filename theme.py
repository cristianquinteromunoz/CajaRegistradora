# theme.py
# Sistema de Diseño Centralizado para Kuro Systems

COLORS = {
    # Fondos
    "bg_main": "#1a1a1a",         # Fondo principal de la app
    "bg_panel": "#212F3D",        # Paneles laterales y menús
    "bg_card": "#2b2b2b",         # Tarjetas y formularios
    "bg_input": "#34495E",        # Cajas de texto
    
    # Acentos y Botones
    "primary": "#2980B9",         # Azul (Botones principales, Búsqueda)
    "primary_hover": "#1F618D",
    "success": "#27AE60",         # Verde (Guardar, Facturar, Ganancias)
    "success_hover": "#1E8449",
    "warning": "#E67E22",         # Naranja (Modificar, Alertas medias)
    "warning_hover": "#D35400",
    "danger": "#C0392B",          # Rojo (Eliminar, Errores, Gastos)
    "danger_hover": "#922B21",
    "special": "#8E44AD",         # Morado (Módulo de Finanzas)
    "special_hover": "#71368A",
    
    # Textos
    "text_main": "#FFFFFF",       # Texto normal
    "text_muted": "gray",         # Texto secundario (placeholders)
    "text_highlight": "#F39C12",  # Textos resaltados (ej. Cambio a devolver)
    
    # Tablas (Zebra Striping)
    "table_header": "#0d0d0d",
    "table_odd": "#1a1a1a",
    "table_even": "#262626",
    "table_selected": "#1f538d",
    "table_danger": "#641E16"
}

# Tamaños de fuente estandarizados
FONTS = {
    "h1": ("Arial", 32, "bold"),       # Títulos grandes (Login, Dashboard)
    "h2": ("Arial", 24, "bold"),       # Títulos de módulos
    "h3": ("Arial", 18, "bold"),       # Subtítulos
    "body": ("Arial", 14, "normal"),   # Texto de lectura
    "body_bold": ("Arial", 14, "bold"),
    "table": ("Arial", 11, "normal"),  # Contenido de tablas
    "table_header": ("Arial", 12, "bold")
}