from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import User
from user.validators import validate_image
from aws.s3_user import get_user_profile_picture_url, set_user_profile_picture
from aws.s3_exceptions import UserProfilePictureNotFound
from user.serializers import (
    UserSerializer,
    CustomLoginSerializer,
    CustomRegisterSerializer
)

from dj_rest_auth.views import PasswordChangeView, PasswordResetView
from dj_rest_auth.registration.views import LoginView, RegisterView
from rest_framework_simplejwt.authentication import JWTAuthentication

class UserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = User.objects.get(user_id=request.user.user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = User.objects.get(user_id=request.user.user_id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfilePictureView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            url = get_user_profile_picture_url(request.user.user_id)
            return Response({'url': url})
        except UserProfilePictureNotFound:
            return Response({'error': 'Imagem de perfil não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        picture = request.FILES['picture']
        picture.name = 'profile_picture' + picture.name[picture.name.rfind('.'):]
        try:
            picture_content = picture.read()
            validate_image(picture_content)
            set_user_profile_picture(request.user.user_id, picture_content, picture.name)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            User.objects.get(email=request.data['email'])
            return Response({'email': ['Este endereço de email já está cadastrado.']}, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_201_CREATED, headers=headers)

class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class CustomPasswordChangeView(PasswordChangeView):
    def post(self, request, *args, **kwargs):
        old_password = request.data.get('old_password', None)

        if old_password is None:
            return Response({'old_password': ['A senha antiga não foi fornecida.']}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            return Response({'old_password': ['Senha antiga incorreta.']}, status=status.HTTP_400_BAD_REQUEST)

        return super().post(request, *args, **kwargs)
    
class CustomPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return super().post(request, *args, **kwargs)
        else:
            return Response({'email': ['Este endereço de email não está cadastrado.']}, status=status.HTTP_400_BAD_REQUEST)