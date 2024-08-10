from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileUploadView, FileViewSet, WebhookView

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('webhook/', WebhookView.as_view(), name='webhook'),
]
