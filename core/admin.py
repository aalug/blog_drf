from django.contrib import admin
from .models import (User, UserProfile,
                     Post, Tag, Comment,
                     PostImage)


admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(PostImage)
