from django.urls import path
from .views import (
    AttendanceReportView, ExportCSVView, ExportPDFView, MonthlySummaryView
)

urlpatterns = [
    path('', AttendanceReportView.as_view(), name='attendance-report'),
    path('export/csv/', ExportCSVView.as_view(), name='export-csv'),
    path('export/pdf/', ExportPDFView.as_view(), name='export-pdf'),
    path('monthly/', MonthlySummaryView.as_view(), name='monthly-summary'),
]
