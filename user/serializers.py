from rest_framework import serializers
from user.models import User
from user.validators import validate_image_base64

from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'user_id',
            'full_name',
            'username',
            'email',
            'profile_picture',
            'date_joined',
            'description'
        )

class CustomRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict['full_name'] = self.validated_data.get('full_name', '')
        return data_dict
    
class CustomLoginSerializer(LoginSerializer):
    email = None

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        user = self.user

        # Ajuste para acessar o campo de identificação primária correto
        data_dict['user_id'] = user.user_id if hasattr(user, 'user_id') else user.id

        return data_dict

class ProfilePictureSerializer(serializers.Serializer):
    picture = serializers.CharField(validators=[validate_image_base64])