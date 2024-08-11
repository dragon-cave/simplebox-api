from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from files.views import WebhookView

urlpatterns = [
    path("api/user/", include('user.urls')),
    path('api/auth/', include('user.auth_urls')),
    path('api/files', include('files.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/webhook/', WebhookView.as_view(), name='webhook'),
]
