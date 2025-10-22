# app/services/pdf_service.py
import os
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from app.config import settings
from app.schemas.video_schema import VideoAnalysisResponse
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        # Create reports directory if it doesn't exist
        os.makedirs(settings.PDF_OUTPUT_PATH, exist_ok=True)
        
        # Define custom styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        self.normal_style = self.styles['Normal']
    
    def generate_report(
        self,
        interview_id: str,
        average_score: float,
        individual_results: List[Dict],
        detailed_analyses: List[VideoAnalysisResponse]
    ) -> str:
        """Generate comprehensive PDF report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{interview_id}_{timestamp}.pdf"
        filepath = os.path.join(settings.PDF_OUTPUT_PATH, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for PDF elements
        elements = []
        
        # Add title
        elements.append(Paragraph(
            f"Video Analysis Report",
            self.title_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add header information
        header_data = [
            ["Interview ID:", interview_id],
            ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Videos Analyzed:", str(len(individual_results))],
            ["Average Genuinity Score:", f"{average_score:.2f}/10"]
        ]
        
        header_table = Table(header_data, colWidths=[2.5*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add summary section
        elements.append(Paragraph("Summary", self.heading_style))
        
        # Score interpretation
        if average_score >= 8:
            score_text = "Excellent - High genuinity detected"
            score_color = colors.green
        elif average_score >= 6:
            score_text = "Good - Acceptable genuinity level"
            score_color = colors.orange
        else:
            score_text = "Poor - Multiple violations detected"
            score_color = colors.red
        
        summary_style = ParagraphStyle(
            'Summary',
            parent=self.normal_style,
            fontSize=12,
            textColor=score_color,
            spaceAfter=10
        )
        elements.append(Paragraph(f"<b>Assessment:</b> {score_text}", summary_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add individual video scores table
        elements.append(Paragraph("Individual Video Scores", self.heading_style))
        
        video_data = [["#", "Video Name", "Duration (s)", "Score", "Penalty"]]
        for idx, result in enumerate(individual_results, 1):
            video_data.append([
                str(idx),
                result['video_name'][:30] + "..." if len(result['video_name']) > 30 else result['video_name'],
                f"{result['total_duration']:.1f}",
                f"{result['genuinity_score']:.2f}",
                f"{result['total_penalty']:.2f}"
            ])
        
        video_table = Table(video_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        video_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(video_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add detailed analysis for videos with errors
        videos_with_errors = [
            analysis for analysis in detailed_analyses
            if len(analysis.detailed_errors) > 0
        ]
        
        if videos_with_errors:
            elements.append(PageBreak())
            elements.append(Paragraph("Detailed Error Analysis", self.heading_style))
            elements.append(Paragraph(
                f"The following {len(videos_with_errors)} video(s) had detected violations:",
                self.normal_style
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            for analysis in videos_with_errors:
                # Video name header
                video_heading = ParagraphStyle(
                    'VideoHeading',
                    parent=self.normal_style,
                    fontSize=13,
                    textColor=colors.HexColor('#2c3e50'),
                    fontName='Helvetica-Bold',
                    spaceAfter=8
                )
                elements.append(Paragraph(f"Video: {analysis.video_name}", video_heading))
                elements.append(Paragraph(
                    f"Score: {analysis.genuinity_score:.2f}/10 | "
                    f"Duration: {analysis.total_duration:.1f}s | "
                    f"Total Penalty: {analysis.total_penalty:.2f}",
                    self.normal_style
                ))
                elements.append(Spacer(1, 0.1*inch))
                
                # Errors table
                if analysis.detailed_errors:
                    error_data = [["Error Type", "From (s)", "To (s)", "Duration (s)", "Confidence"]]
                    for error in analysis.detailed_errors:
                        duration = error.to_time - error.from_time
                        error_data.append([
                            error.error_type.replace('_', ' ').title(),
                            f"{error.from_time:.1f}",
                            f"{error.to_time:.1f}",
                            f"{duration:.1f}",
                            f"{error.confidence:.2f}"
                        ])
                    
                    error_table = Table(error_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
                    error_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightpink),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8)
                    ]))
                    elements.append(error_table)
                
                # Error summary
                if analysis.errors_summary:
                    elements.append(Spacer(1, 0.15*inch))
                    elements.append(Paragraph("<b>Error Summary:</b>", self.normal_style))
                    
                    for error_type, summary in analysis.errors_summary.items():
                        if summary:
                            summary_text = f"• {error_type.replace('_', ' ').title()}: "
                            details = []
                            for key, value in summary.items():
                                details.append(f"{key}={value:.2f}")
                            summary_text += ", ".join(details)
                            elements.append(Paragraph(summary_text, self.normal_style))
                
                elements.append(Spacer(1, 0.3*inch))
        else:
            elements.append(Paragraph(
                "<b>No violations detected in any video!</b>",
                ParagraphStyle('GoodNews', parent=self.normal_style, textColor=colors.green, fontSize=12)
            ))
        
        # Add footer
        elements.append(PageBreak())
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.normal_style,
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Report generated by {settings.COMPANY_NAME}<br/>"
            f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        logger.info(f"PDF report generated successfully: {filepath}")
        
        return filepath
