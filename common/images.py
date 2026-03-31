import io
import os
from PIL import Image
import pillow_heif
from django.core.files.base import ContentFile

# Registrar el soporte para HEIC/HEIF (iPhone) globalmente
pillow_heif.register_heif_opener()

def convert_uploaded_image_to_webp(uploaded_file):
    """
    Recibe un archivo subido (UploadedFile) y lo convierte a formato WebP lossless.
    Si la conversión falla o no es una imagen válida, devuelve el archivo original.
    """
    try:
        # Abrir la imagen desde el archivo subido
        img = Image.open(uploaded_file)
        
        # Manejar transparencia: RGBA para imágenes con alfa, RGB para el resto
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        
        # Guardar en un buffer de memoria
        output = io.BytesIO()
        img.save(output, format="WEBP", lossless=True, quality=100)
        
        # Generar el nuevo nombre con extensión .webp
        new_name = os.path.splitext(uploaded_file.name)[0] + ".webp"
        return ContentFile(output.getvalue(), name=new_name)
    except Exception:
        # En caso de error (ej. formato no soportado), retornamos el original para no romper el flujo
        return uploaded_file