# app/services/content_formatter.py

class ContentFormatter:
    """
    Clase de utilidad para formatear texto y asegurar que cumpla con
    las restricciones de la API de WhatsApp.
    """
    # Límites de caracteres de la API de WhatsApp
    HEADER_LIMIT = 60
    BODY_LIMIT = 1024
    FOOTER_LIMIT = 60
    SECTION_TITLE_LIMIT = 24
    ROW_TITLE_LIMIT = 24
    ROW_DESCRIPTION_LIMIT = 72
    BUTTON_TEXT_LIMIT = 20

    @staticmethod
    def truncate(text: str, limit: int) -> str:
        """
        Trunca un texto a un límite específico, añadiendo '...' si es necesario,
        asegurando que el resultado final no exceda el límite.
        """
        if not text:
            return ""
        if len(text) <= limit:
            return text
        else:
            # Dejamos espacio para los tres puntos '...'
            return text[:limit - 3] + "..."