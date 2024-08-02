from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import User
from user.serializers import ProfilePictureSerializer
from aws.s3 import hello_world
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
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({'url': hello_world()})

    def put(self, request):
        serializer = ProfilePictureSerializer(data=request.data)
        if serializer.is_valid():
            return Response()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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