from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, WebhookView

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    # path('webhook/', WebhookView.as_view(), name='webhook'),
]
