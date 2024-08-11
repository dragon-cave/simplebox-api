from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, WebhookView

router = DefaultRouter()
router.register(r'teste', FileViewSet, basename='file')

urlpatterns = [
    path('teste/', include(router.urls)),
    # path('webhook/', WebhookView.as_view(), name='webhook'),
]
