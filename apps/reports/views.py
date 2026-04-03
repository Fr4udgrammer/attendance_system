import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from apps.attendance.models import Attendance
from apps.employees.models import Employee
from apps.reports.serializers import ReportFilterSerializer, AttendanceReportSerializer


class AttendanceReportView(APIView):
    """Generate attendance report with filters."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        ).all()

        start_date = request.query_params.get('from') or request.query_params.get('start_date')
        end_date = request.query_params.get('to') or request.query_params.get('end_date')
        status_filter = request.query_params.get('status')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        total_records = queryset.count()
        present_count = queryset.filter(status='present').count()
        late_count = queryset.filter(status='late').count()
        absent_count = queryset.filter(status='absent').count()
        half_day_count = queryset.filter(status='half_day').count()

        avg_duration = queryset.aggregate(avg=Avg('check_out') - Avg('check_in'))['avg']
        avg_hours = 0
        if avg_duration and avg_duration.total_seconds() > 0:
            avg_hours = round(avg_duration.total_seconds() / 3600, 1)

        total = Employee.objects.filter(status='active').count()
        attendance_rate = (present_count + late_count) / total * 100 if total > 0 else 0

        return Response({
            'total_records': total_records,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'half_day_count': half_day_count,
            'average_duration': avg_hours,
            'attendance_rate': round(attendance_rate, 1),
        })


class ExportCSVView(APIView):
    """Export attendance data to CSV."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Name', 'Department', 'Date',
            'Check In', 'Check Out', 'Status', 'Notes'
        ])

        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        ).all()

        start_date = request.query_params.get('start_date') or request.query_params.get('from')
        end_date = request.query_params.get('end_date') or request.query_params.get('to')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        for record in queryset:
            writer.writerow([
                record.employee.employee_id,
                record.employee.user.get_full_name(),
                record.employee.department.name,
                record.date,
                record.check_in.strftime('%H:%M') if record.check_in else '-',
                record.check_out.strftime('%H:%M') if record.check_out else '-',
                record.status,
                record.notes
            ])

        return response


class ExportPDFView(APIView):
    """Export attendance data to PDF."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#00f5ff')
        )

        elements.append(Paragraph("Attendance Report", title_style))
        elements.append(Spacer(1, 20))

        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        ).all()

        start_date = request.query_params.get('start_date') or request.query_params.get('from')
        end_date = request.query_params.get('end_date') or request.query_params.get('to')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        queryset = queryset[:100]

        data = [['Employee', 'Department', 'Date', 'Status', 'Check In', 'Check Out']]
        for record in queryset:
            data.append([
                record.employee.user.get_full_name(),
                record.employee.department.name,
                record.date.strftime('%Y-%m-%d'),
                record.status.title(),
                record.check_in.strftime('%H:%M') if record.check_in else '-',
                record.check_out.strftime('%H:%M') if record.check_out else '-',
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00f5ff')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#00f5ff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#16213e'), colors.HexColor('#1a1a2e')]),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
        return response


class MonthlySummaryView(APIView):
    """Get monthly attendance summary."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        start_date = timezone.datetime(year, month, 1).date()
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1).date() - timezone.timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1).date() - timezone.timedelta(days=1)

        records = Attendance.objects.filter(date__gte=start_date, date__lte=end_date)

        total_days = (end_date - start_date).days + 1
        total_present = records.filter(status__in=['present', 'late']).count()
        total_late = records.filter(status='late').count()
        total_absent = records.filter(status='absent').count()

        total_employees = Employee.objects.filter(status='active').count()
        expected_total = total_employees * total_days
        avg_rate = (total_present / expected_total * 100) if expected_total > 0 else 0

        return Response({
            'month': start_date.strftime('%B'),
            'year': year,
            'total_days': total_days,
            'total_present': total_present,
            'total_late': total_late,
            'total_absent': total_absent,
            'average_attendance_rate': round(avg_rate, 1)
        })
