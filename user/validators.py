from io import BytesIO
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

def validate_image(image_data):
    try:
        image = Image.open(BytesIO(image_data))
        image.verify()
    except Image.UnidentifiedImageError:
        raise ValidationError(
            _("Imagem inválida"),
            code='invalid_image'
        )
