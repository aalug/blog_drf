"""
URL mappings for the posts' app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from posts import views

router = DefaultRouter()
router.register('posts', views.PostsViewSet)

app_name = 'posts'

urlpatterns = [
    path('', include(router.urls)),
]
