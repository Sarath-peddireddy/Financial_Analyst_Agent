from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from typing import Dict, Any, List

class PDFReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='DataPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceBefore=5,
            spaceAfter=5
        ))
    
    def generate_investment_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a PDF investment report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"investment_report_{report_data['ticker']}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        title = f"Investment Analysis Report: {report_data['ticker']}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Real-time stock data section
        if 'stock_data' in report_data and not report_data['stock_data'].get('error'):
            stock_data = report_data['stock_data']
            story.append(Paragraph("Current Market Data", self.styles['SectionHeader']))
            
            current_data = [
                ['Current Price:', f"${stock_data['price']:.2f}"],
                ['Daily Change:', f"${stock_data['change']:.2f} ({stock_data['change_percent']:.2f}%)"],
                ['Volume:', f"{stock_data.get('volume', 'N/A')}"],
                ['Previous Close:', f"${stock_data['previous_close']:.2f}"]
            ]
            
            stock_table = Table(current_data, colWidths=[2*inch, 2*inch])
            stock_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stock_table)
            story.append(Spacer(1, 20))
        
        # Company information section
        if 'company_info' in report_data and not report_data['company_info'].get('error'):
            company_info = report_data['company_info']
            story.append(Paragraph("Company Information", self.styles['SectionHeader']))
            
            company_data = [
                ['Company Name:', company_info.get('name', 'N/A')],
                ['Sector:', company_info.get('sector', 'N/A')],
                ['Industry:', company_info.get('industry', 'N/A')],
                ['Market Cap:', str(company_info.get('market_cap', 'N/A'))],
                ['P/E Ratio:', str(company_info.get('pe_ratio', 'N/A'))],
                ['Beta:', str(company_info.get('beta', 'N/A'))]
            ]
            
            company_table = Table(company_data, colWidths=[2*inch, 3*inch])
            company_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(company_table)
            story.append(Spacer(1, 20))
        
        # Report metadata
        metadata_data = [
            ['Report Date:', datetime.now().strftime("%B %d, %Y")],
            ['Ticker Symbol:', report_data['ticker']],
            ['Query:', report_data['question']],
            ['Analysis Type:', 'AI-Powered Investment Analysis']
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Performance chart (if historical data available)
        if 'historical_data' in report_data and report_data['historical_data']:
            chart_path = self._generate_price_chart(report_data['historical_data'], report_data['ticker'])
            if chart_path:
                from reportlab.platypus import Image
                story.append(Paragraph("Price Performance Chart", self.styles['SectionHeader']))
                story.append(Image(chart_path, width=6*inch, height=3*inch))
                story.append(Spacer(1, 20))
        
        # Main analysis content
        story.append(Paragraph("Investment Analysis", self.styles['SectionHeader']))
        
        # Split the report content into paragraphs
        content_paragraphs = report_data['report_content'].split('\n\n')
        for paragraph in content_paragraphs:
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), self.styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Risk score
        risk_score = report_data.get('risk_score')
        if isinstance(risk_score, int):
            risk_table = Table([
                ['Risk Score (0=Low, 10=High):', str(risk_score)]
            ], colWidths=[3*inch, 1*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral if risk_score >= 7 else colors.lightyellow if risk_score >= 4 else colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(Paragraph("Risk Assessment", self.styles['SectionHeader']))
            story.append(risk_table)
            story.append(Spacer(1, 20))

        # Disclaimer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Important Disclaimer", self.styles['SectionHeader']))
        disclaimer = """This report is generated by an AI system for educational and informational purposes only. 
        It does not constitute personalized financial advice, investment recommendations, or professional investment counsel. 
        Past performance does not guarantee future results. All investments carry risk of loss. 
        Please consult with a qualified financial advisor before making investment decisions."""
        
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _generate_price_chart(self, historical_data: List[Dict[str, Any]], ticker: str) -> str:
        """Generate a price chart from historical data."""
        try:
            if not historical_data:
                return None
            
            # Prepare data for plotting
            dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in historical_data]
            prices = [item['close'] for item in historical_data]
            
            # Create the plot
            plt.figure(figsize=(10, 6))
            plt.plot(dates, prices, linewidth=2, color='#667eea')
            plt.title(f'{ticker} Price Performance', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Price ($)', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.xticks(rotation=45)
            
            # Save chart
            chart_filename = f"chart_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            chart_path = os.path.join(self.output_dir, chart_filename)
            plt.tight_layout()
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None
    
    def cleanup_old_reports(self, max_age_hours: int = 24):
        """Clean up old report files."""
        if not os.path.exists(self.output_dir):
            return
        
        current_time = datetime.now().timestamp()
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > (max_age_hours * 3600):  # Convert hours to seconds
                    os.remove(filepath)