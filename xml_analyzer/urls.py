from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('upload-report/', views.upload_report, name='upload_report'),  
    path('results/summary/', views.results_summary_view, name='results_summary'),
    path('results/<str:status>/', views.results_status_view, name='results_by_status'),
    path('rerun/', views.rerun_view, name='rerun_page'),
    path('rerun/download/', views.download_final_report, name='download_final_report'),
    path("results/status/<str:status>/", views.results_status_view, name="results_status"),
    path("rerun/", views.rerun_view, name="rerun_view"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)