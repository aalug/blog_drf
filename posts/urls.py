"""
URL mappings for the posts' app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from posts import views

router = DefaultRouter()
router.register('posts', views.PostsViewSet)
router.register('tags', views.TagViewSet)
router.register('comments', views.CommentViewSer)
router.register('postimages', views.PostImageViewSet)
router.register('votes', views.VoteViewSet)

app_name = 'posts'

urlpatterns = [
    path('', include(router.urls)),
]
