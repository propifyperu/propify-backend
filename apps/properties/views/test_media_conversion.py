import io
import json
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.properties.models import Property, PropertyMedia

class ImageConversionTest(APITestCase):
    def setUp(self):
        # Crear usuario y autenticar
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.client.force_authenticate(user=self.user)
        
        # Crear una propiedad mínima para la prueba
        # Nota: Asegúrate de que los campos obligatorios de tu modelo Property coincidan
        self.property = Property.objects.create(
            title="Propiedad de Prueba",
            price=100000,
            responsible=self.user
        )
        self.url = reverse('propertymedia-list')

    def test_upload_converts_to_webp(self):
        """Verifica que al subir un PNG se guarda como WEBP"""
        # 1. Crear una imagen PNG real en memoria
        file_io = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(255, 0, 0, 255))
        image.save(file_io, 'PNG')
        file_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_image.png",
            file_io.read(),
            content_type="image/png"
        )

        # 2. Enviar al endpoint
        data = {
            "property": self.property.id,
            "media_files": [uploaded_file],
            "media_metadata": json.dumps([
                {"title": "Foto Test", "label": "test", "order": 1, "media_type": "image"}
            ])
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        # 3. Aserciones
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        media_obj = PropertyMedia.objects.get(property=self.property)
        self.assertTrue(media_obj.file.name.endswith('.webp'), "El archivo no se guardó con extensión .webp")
        self.assertEqual(media_obj.media_type, "image")