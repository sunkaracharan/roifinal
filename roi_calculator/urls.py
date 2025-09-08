
"""roi_calculator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from calculator import views as calculator_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', calculator_views.custom_logout, name='logout'),
    path('register/', calculator_views.register, name='register'),
    
    # Public pages (no authentication required)
    path('', calculator_views.home_page, name='landing'),
    path('contact/', calculator_views.contact_page, name='contact'),
    
    # Protected dashboard routes (authentication required)
    path('dashboard/', include('calculator.urls')),
    path('dashboard/history/analysis/', calculator_views.history_analysis, name='history_analysis'),
    path('dashboard/history/analysis/data/', calculator_views.history_analysis_data, name='history_analysis_data'),
]
