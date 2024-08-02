import base64
from io import BytesIO
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

def validate_image_base64(image_data):
    try:
        image_data = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_data))
        image.verify()
    except (base64.binascii.Error, Image.UnidentifiedImageError):
        raise ValidationError(
            _("Imagem inválida"),
            code='invalid_image'
        )
