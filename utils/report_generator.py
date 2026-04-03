import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from database.db_handler import connect_db, get_app_settings, CURRENT_SHOP_ID

def generate_daily_report(target_date):
    """
    Fetches daily stats and generates a professional PDF report.
    Args:
        target_date (datetime | str): Date to generate report for (e.g., 'YYYY-MM-DD').
    Returns:
        str: Path to the generated PDF file.
    """
    if isinstance(target_date, str):
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target_date_obj = target_date

    date_str = target_date_obj.strftime("%Y-%m-%d")
    
    # 1. FETCH DATA FROM DATABASE
    stats = fetch_daily_stats(date_str)
    shop_info = get_app_settings()
    
    # 2. FILE STORAGE SETUP
    reports_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    filename = f"Daily_Report_{date_str}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    # 3. PDF CREATION (REPORTLAB)
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#1b4d89"),
        alignment=1, # Centered
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=1, # Centered
        spaceAfter=25
    )

    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#1b4d89"),
        spaceBefore=20,
        spaceAfter=15
    )

    # PAGE 1: Branding and Headers
    shop_name = shop_info.get("shop_name", "Kamran and Sohail Electronics")
    shop_address = shop_info.get("shop_address", "Main St, Hub")
    
    elements.append(Paragraph(shop_name.upper(), title_style))
    elements.append(Paragraph(shop_address, subtitle_style))
    elements.append(Paragraph(f"🗓️ DAILY PERFORMANCE REPORT - {date_str}", header_style))
    elements.append(Spacer(1, 15))
    
    # PAGE 2: Summary Table (Sales vs Repairs)
    data = [
        ["Category", "Items/Count", "Total Revenue (Rs.)"],
        ["Product Sales", str(stats['sales_count']), f"{stats['sales_amount']:,.2f}"],
        ["Repairs Finalized", str(stats['repairs_count']), f"{stats['repairs_amount']:,.2f}"],
        ["Total Income", "-", f"{stats['total_income']:,.2f}"]
    ]
    
    summary_table = Table(data, colWidths=[200, 100, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1b4d89")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#1b4d89")), # Footer color
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # PAGE 3: Profitability Analysis
    elements.append(Paragraph("💹 Profitability Overview", header_style))
    
    profit_data = [
        ["Metric", "Value (Rs.)"],
        ["Gross Income", f"{stats['total_income']:,.2f}"],
        ["Stock/COGS Cost", f"- {stats['stock_cost']:,.2f}"],
        ["Repair Parts cost", f"- {stats['repair_parts_cost']:,.2f}"],
        ["Operating Expenses", f"- {stats['operating_expenses']:,.2f}"],
        ["NET PROFIT", f"{stats['net_profit']:,.2f}"]
    ]
    
    profit_table = Table(profit_data, colWidths=[250, 150])
    profit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00a3af")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor("#2ecc71") if stats['net_profit'] > 0 else colors.red)
    ]))
    
    elements.append(profit_table)
    
    # FOOTER
    elements.append(Spacer(1, 60))
    footer_text = f"Software generated report | Shop ID: {CURRENT_SHOP_ID} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # BUILD PDF
    doc.build(elements)
    
    return filepath

def fetch_daily_stats(date_str):
    """
    Detailed database queries to calculate day-specific metrics.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    stats = {
        'sales_amount': 0.0,
        'sales_count': 0,
        'repairs_amount': 0.0,
        'repairs_count': 0,
        'stock_cost': 0.0,
        'repair_parts_cost': 0.0,
        'operating_expenses': 0.0,
        'total_income': 0.0,
        'net_profit': 0.0
    }
    
    try:
        # 1. Total Sales and Repairs from Bill_Items
        # bi.Price is already row total (Price * Qty)
        query_items = """
            SELECT bi.Type, SUM(bi.Price), COUNT(*) 
            FROM Bill_Items bi 
            JOIN Bills b ON bi.Bill_ID = b.Bill_ID 
            WHERE DATE(b.Timestamp) = %s AND b.Shop_ID = %s 
            GROUP BY bi.Type
        """
        cursor.execute(query_items, (date_str, CURRENT_SHOP_ID))
        for row in cursor.fetchall():
            if row[0] == 'Product':
                stats['sales_amount'] = float(row[1] or 0.0)
                stats['sales_count'] = row[2]
            elif row[0] == 'Repair':
                stats['repairs_amount'] = float(row[1] or 0.0)
                stats['repairs_count'] = row[2]

        # 2. Stock Cost (COGS)
        query_cogs = """
            SELECT SUM(p.Purchase_Price * bi.Quantity) 
            FROM Bill_Items bi 
            JOIN Bills b ON bi.Bill_ID = b.Bill_ID 
            JOIN Products p ON (bi.Source_ID = p.Product_ID OR (bi.Source_ID IS NULL AND bi.Description = p.Name))
            WHERE bi.Type = 'Product' AND DATE(b.Timestamp) = %s AND b.Shop_ID = %s
        """
        cursor.execute(query_cogs, (date_str, CURRENT_SHOP_ID))
        stats['stock_cost'] = float(cursor.fetchone()[0] or 0.0)

        # 3. Repair Parts Cost
        query_rep_cost = """
            SELECT SUM(r.spent_cost) 
            FROM Bill_Items bi 
            JOIN Bills b ON bi.Bill_ID = b.Bill_ID 
            JOIN Repairs r ON bi.Source_ID = r.id 
            WHERE bi.Type = 'Repair' AND DATE(b.Timestamp) = %s AND b.Shop_ID = %s
        """
        cursor.execute(query_rep_cost, (date_str, CURRENT_SHOP_ID))
        stats['repair_parts_cost'] = float(cursor.fetchone()[0] or 0.0)

        # 4. Operating Expenses
        query_exp = "SELECT SUM(Amount) FROM Expenses WHERE DATE(Timestamp) = %s AND Shop_ID = %s"
        cursor.execute(query_exp, (date_str, CURRENT_SHOP_ID))
        stats['operating_expenses'] = float(cursor.fetchone()[0] or 0.0)

        # 5. Final Calculations
        stats['total_income'] = stats['sales_amount'] + stats['repairs_amount']
        total_costs = stats['stock_cost'] + stats['repair_parts_cost'] + stats['operating_expenses']
        stats['net_profit'] = stats['total_income'] - total_costs

    finally:
        conn.close()
        
    return stats
