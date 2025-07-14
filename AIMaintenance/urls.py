from django.contrib import admin
from django.urls import path , include
from AIMaintenance import views as v
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('predictive/',include('predictive.urls')),
    path('',v.home),
]+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
