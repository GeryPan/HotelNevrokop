from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Check if this exact line is here and not commented out
    path('', include('hotel_system.urls')),
]
