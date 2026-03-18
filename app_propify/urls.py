from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Propify API",
        default_version="v1",
        description="API REST para el sistema Propify",
    ),
    public=True,
    permission_classes=[AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/auth/", include("apps.users.urls_auth")),
    path("api/users/", include("apps.users.urls")),
    path("api/locations/", include("apps.locations.urls")),
    path("api/catalogs/", include("apps.catalogs.urls")),
    path("api/properties/", include("apps.properties.urls")),
    path("api/crm/", include("apps.crm.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

# Servir archivos media en local (solo cuando MEDIA_URL es local, no Azure)
if settings.DEBUG and settings.MEDIA_URL.startswith("/"):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
