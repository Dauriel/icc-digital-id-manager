"""id_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from manager import views

router = DefaultRouter()
router.register(r"schema", views.SchemaViewSet)
router.register(r"credential-definition", views.CredentialDefinitionViewSet)

urlpatterns = [
    path(
        "credential-request",
        views.CredentialRequestListCreateAPIView.as_view(),
        name="CredentialRequestListCreate",
    ),
    path(
        "credential-request/<int:pk>",
        views.CredentialRequestRetrieveAPIView.as_view(),
        name="CredentialRequestRetrieve",
    ),
    path("connection-check", views.ConnectionCheck.as_view(), name="ConnectionCheck",),
    path("credential-check", views.CredentialCheck.as_view(), name="CredentialCheck",),
    path("credential-obtain", views.credential_obtain, name="CredentialObtain"),
    path("webhooks/topic/<str:topic>/", views.webhooks, name="webhooks"),
    path("", include(router.urls)),
]
