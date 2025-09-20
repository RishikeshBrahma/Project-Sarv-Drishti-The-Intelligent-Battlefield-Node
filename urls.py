"""
URL configuration for drishti_project project.
"""
# from django.contrib import admin
# from django.urls import path, include
# from api.views import frontend_view # Correctly import the view for the frontend

# # urlpatterns = [
# #     path('admin/', admin.site.urls),
# #     # Route for the main frontend page
# #     path('', frontend_view, name='frontend'),
# #     # Include all URLs from the 'api' app under the 'api/v1/' prefix
# #     path('api/v1/', include('api.urls')),
# # ]
# # from django.contrib import admin
# # from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('api.urls')),  # <-- Point root traffic to the api app
# ]
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This is the correct way to handle app routing.
    # It tells Django to look in 'api/urls.py' for all further URL patterns.
    path('', include('api.urls')),
]


