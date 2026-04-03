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
        user = request.user
        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        )

        if not user.is_admin:
            if user.is_manager:
                queryset = queryset.filter(employee__department=user.department)
            else:
                queryset = queryset.filter(employee__user=user)

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
        user = request.user
        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        )

        if not user.is_admin:
            if user.is_manager:
                queryset = queryset.filter(employee__department=user.department)
            else:
                queryset = queryset.filter(employee__user=user)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Name', 'Department', 'Date',
            'Check In', 'Check Out', 'Status', 'Notes'
        ])

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

        user = request.user
        queryset = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        )

        if not user.is_admin:
            if user.is_manager:
                queryset = queryset.filter(employee__department=user.department)
            else:
                queryset = queryset.filter(employee__user=user)

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
        try:
            year = int(request.query_params.get('year', timezone.now().year))
            month = int(request.query_params.get('month', timezone.now().month))
            
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
            if not (2000 <= year <= 2100):
                raise ValueError("Year must be between 2000 and 2100")
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        start_date = timezone.datetime(year, month, 1).date()
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1).date() - timezone.timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1).date() - timezone.timedelta(days=1)

        user = self.request.user
        records = Attendance.objects.filter(date__gte=start_date, date__lte=end_date)
        
        if not user.is_admin:
            if user.is_manager:
                records = records.filter(employee__department=user.department)
            else:
                records = records.filter(employee__user=user)

        total_days = (end_date - start_date).days + 1
        total_present = records.filter(status__in=['present', 'late']).count()
        total_late = records.filter(status='late').count()
        total_absent = records.filter(status='absent').count()

        if user.is_admin or user.is_manager:
            total_employees = Employee.objects.filter(status='active').all()
            if user.is_manager:
                total_employees = total_employees.filter(department=user.department)
            total_count = total_employees.count()
        else:
            total_count = 1

        expected_total = total_count * total_days
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


class ExportDTRView(APIView):
    """Export Daily Time Record (CSC Form No. 48) to PDF."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee_id = request.query_params.get('employee_id')
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        if employee_id and (user.is_admin or user.is_manager):
            try:
                employee = Employee.objects.get(id=employee_id)
                if user.is_manager and employee.department != user.department:
                    return Response({'error': 'Unauthorized access to employee data'}, status=403)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found'}, status=404)
        else:
            if not hasattr(user, 'employee'):
                return Response({'error': 'Employee profile not found'}, status=400)
            employee = user.employee

        start_date = timezone.datetime(year, month, 1).date()
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1).date() - timezone.timedelta(days=1)
        else:
            end_date = timezone.datetime(year, month + 1, 1).date() - timezone.timedelta(days=1)

        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Civil Service Form No. 48", styles['Normal']))
        elements.append(Paragraph("<b>DAILY TIME RECORD</b>", styles['Title']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(f"<b>NAME:</b> {employee.full_name.upper()}", styles['Normal']))
        elements.append(Paragraph(f"For the month of: {start_date.strftime('%B %Y')}", styles['Normal']))
        elements.append(Spacer(1, 10))

        data = [
            ['Day', 'AM Arrival', 'AM Departure', 'PM Arrival', 'PM Departure', 'Undertime']
        ]

        total_days = (end_date - start_date).days + 1
        for day in range(1, total_days + 1):
            curr_date = timezone.datetime(year, month, day).date()
            record = attendance_records.filter(date=curr_date).first()
            
            row = [str(day)]
            if record:
                # Simplified DTR logic for now
                arrival = record.check_in.strftime('%H:%M') if record.check_in else '-'
                departure = record.check_out.strftime('%H:%M') if record.check_out else '-'
                
                # Split AM/PM based on 12:00
                if record.check_in and record.check_in.hour < 12:
                    row.append(arrival)
                    row.append("12:00") # Dummy departure
                else:
                    row.append("-")
                    row.append("-")
                    
                if record.check_out and record.check_out.hour >= 12:
                    row.append("13:00") # Dummy arrival
                    row.append(departure)
                else:
                    row.append("-")
                    row.append("-")
                
                row.append(str(record.penalty_minutes) if record.penalty_minutes > 0 else "0")
            else:
                row.extend(['-', '-', '-', '-', '0'])
            
            data.append(row)

        table = Table(data, colWidths=[30, 80, 80, 80, 80, 60])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("I certify on my honor that the above is a true and correct report...", styles['Normal']))
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("__________________________", styles['Normal']))
        elements.append(Paragraph("Verified as to the prescribed office hours:", styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f"DTR_{employee.employee_id}_{start_date.strftime('%Y_%m')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
