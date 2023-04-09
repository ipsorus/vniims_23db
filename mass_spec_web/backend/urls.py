from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('upload/', views.upload_spectrum, name='upload'),
    path('upload/metadata/<int:id>/',
         views.upload_metadata, name='upload_metadata'),
    path('upload/fields/<int:id>/', views.upload_fields, name='upload_fields'),
    path('upload/peaks/<int:id>/', views.upload_peaks, name='upload_peaks'),
    path('upload/review/<int:id>/', views.upload_review, name='upload_review'),
    path('display/viewSpectrum1/<int:id>/', views.view_spectrum, name='viewSpectrum1'),
    path('spectrum_list/', views.spectrum_list, name='spectrum_list'),
    path('display/', views.view_spectrum1, name='display'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login')
]
