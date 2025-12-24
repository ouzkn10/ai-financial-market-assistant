import pandas as pd
import io
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from openpyxl import Workbook

# --- STYLE DEFIINITIONS ---
styles = getSampleStyleSheet()
style_title = ParagraphStyle('T', parent=styles['Title'], fontSize=24, textColor=colors.HexColor("#0c2461"), spaceAfter=15) # SpaceAfter azaltıldı
style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor("#002060"), spaceBefore=5) # SpaceBefore azaltıldı
style_body = ParagraphStyle('B', parent=styles['BodyText'], fontSize=10, leading=14)
style_disclaimer = ParagraphStyle('D', parent=styles['BodyText'], fontSize=7, textColor=colors.grey, alignment=1)
style_green = ParagraphStyle('G', parent=styles['BodyText'], textColor=colors.darkgreen, fontSize=9)
style_red = ParagraphStyle('R', parent=styles['BodyText'], textColor=colors.darkred, fontSize=9)

# --- FOOTER: PAGE NUMBER ---
def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = "Page %d" % page_num
    canvas.saveState()
    
    # Footer
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(200*mm, 5*mm, text) 
    canvas.drawString(10*mm, 5*mm, "AXIOM QUANT PARTNERS | Private & Confidential")
    
    # Watermark (CONFIDENTIAL)
    canvas.setFont("Helvetica-Bold", 60)
    canvas.setFillColor(colors.lightgrey, alpha=0.2)
    canvas.translate(100*mm, 150*mm)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    
    canvas.restoreState()

# --- PROGRESS BAR ---
class ProgressBar(Flowable):
    def __init__(self, pct, color):
        self.pct = min(max(pct,0),1)
        self.color = color
        self.width = 30*mm 
        self.height = 4*mm
    def wrap(self, availWidth, availHeight): return self.width, self.height
    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(colors.lightgrey)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width*self.pct, self.height, fill=1, stroke=0)
        self.canv.restoreState()

# --- VISUAL RISK/REWARD SPECTRUM ---
class RiskRewardSpectrum(Flowable):
    def __init__(self, stop, entry, target, current):
        self.stop = stop
        self.entry = entry
        self.target = target
        self.current = current
        self.width = 160*mm
        self.height = 15*mm
        
    def wrap(self, availWidth, availHeight): return self.width, self.height
    
    def draw(self):
        self.canv.saveState()
        total_range = self.target - self.stop
        if total_range == 0: total_range = 1 
        
        risk_ratio = abs(self.entry - self.stop) / abs(total_range)
        reward_ratio = abs(self.target - self.entry) / abs(total_range)
        
        risk_width = self.width * risk_ratio
        reward_width = self.width * reward_ratio
        
        # Spacing
        self.canv.setFillColor(colors.HexColor("#ffcdd2")) 
        self.canv.rect(0, self.height/3, risk_width, self.height/3, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor("#c8e6c9")) 
        self.canv.rect(risk_width, self.height/3, reward_width, self.height/3, fill=1, stroke=0)
        
        # Lines and Texts
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(1)
        self.canv.line(risk_width, self.height/3, risk_width, self.height*2/3)
        self.canv.setFillColor(colors.black)
        self.canv.setFont("Helvetica-Bold", 8)
        self.canv.drawCentredString(risk_width, self.height*2/3 + 2, "ENTRY")
        
        self.canv.setFillColor(colors.red)
        self.canv.drawString(0, self.height/3 - 8, f"STOP: ${self.stop:.2f}")
        self.canv.setFillColor(colors.green)
        self.canv.drawRightString(self.width, self.height/3 - 8, f"TARGET: ${self.target:.2f}")
        
        if abs(total_range) > 0:
            curr_pct = abs(self.current - self.stop) / abs(total_range)
            curr_pct = min(max(curr_pct, 0), 1)
            curr_pos = curr_pct * self.width
            
            self.canv.setFillColor(colors.HexColor("#002060"))
            p = self.canv.beginPath()
            p.moveTo(curr_pos, self.height) 
            p.lineTo(curr_pos - 4, self.height - 5)
            p.lineTo(curr_pos + 4, self.height - 5)
            p.close()
            self.canv.drawPath(p, fill=1, stroke=0)
            
            self.canv.setFont("Helvetica-Bold", 9)
            self.canv.drawCentredString(curr_pos, self.height + 2, f"${self.current:.2f}")
        
        self.canv.restoreState()

def build_full_report(pdf, xlsx, summary, trades, signals, equity, benchmark, portfolio_weights=None, market_metrics=None):
    doc = SimpleDocTemplate(pdf, pagesize=A4, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=7*mm)
    elems = []
    
    # --- PAGE 1: SUMMARY ---
    elems.append(Paragraph("AXIOM QUANT: PROBABILISTIC EDGE", style_title))
    
    # 1. GRAPH 
    plt.style.use('seaborn-v0_8-white')
    fig, ax = plt.subplots(figsize=(10, 3.5)) 
    common = equity.index.intersection(benchmark.index)
    if not common.empty:
        e = equity.loc[common]
        b = benchmark.loc[common]
        e = (e / e.iloc[0]) * 100
        b = (b / b.iloc[0]) * 100
        ax.plot(e, label='Axiom Quant-V (Algo Strategy)', color='#00BFFF', linewidth=2.5) 
        ax.fill_between(e.index, e, 100, color='#00BFFF', alpha=0.1)
        ax.plot(b, label='Market (QQQ)', color='#000080', linewidth=2.0) 
    
    ax.set_title("Cumulative Performance (Rebased to 100)", fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', frameon=True)
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=True)
    buf.seek(0)
    elems.append(Image(buf, width=190*mm, height=60*mm))
    plt.close()
    
    elems.append(Spacer(1, 3*mm))
    
    # 2. TABLES 
    m_cagr = market_metrics.get('cagr', 0)
    m_sharpe = market_metrics.get('sharpe', 0)
    m_mdd = market_metrics.get('mdd', 0)
    
    kpi_data = [
        ["METRIC", "STRATEGY", "MARKET"],
        ["CAGR", f"{summary.get('cagr',0):.1f}%", f"{m_cagr:.1f}%"],
        ["Sharpe", f"{summary.get('sharpe',0):.2f}", f"{m_sharpe:.2f}"],
        ["Max DD", f"{summary.get('mdd',0):.1f}%", f"{m_mdd:.1f}%"],
        ["Alpha vs QQQ", f"{summary.get('alpha',0)*100:.1f}%", "-"],
        ["Port. Beta", f"{summary.get('beta',0):.2f}", "1.00"],
        ["Win Rate", f"{summary.get('win_rate',0)*100:.1f}%", "-"],
        ["Total Trades", f"{summary.get('total_trades',0)}", "-"]
    ]
    t_kpi = Table(kpi_data, colWidths=[45*mm, 25*mm, 25*mm])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#002060")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ALIGN',(1,0),(-1,-1),'CENTER'),
        ('FONTSIZE',(0,0),(-1,-1),9)
    ]))
    
    signal_tickers = [s['ticker'] for s in signals]
    alloc_data = [["TOP HOLDINGS", "WEIGHT", "RISK ($)"]]
    
    count = 0
    if portfolio_weights:
        for t, w in portfolio_weights:
            if t in signal_tickers:
                alloc_data.append([t, f"{w*100:.1f}%", f"${int(w*100000):,}"])
                count += 1
            if count >= 7: break
            
    t_alloc = Table(alloc_data, colWidths=[30*mm, 25*mm, 30*mm])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#002060")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ALIGN',(1,0),(-1,-1),'RIGHT'),
        ('FONTSIZE',(0,0),(-1,-1),9)
    ]))
    
    t_main = Table([[t_kpi, Spacer(20*mm,0), t_alloc]])
    t_main.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elems.append(t_main)
    
    elems.append(Spacer(1, 3*mm))
    
    # 3. PIE CHART 
    labels = ['Technology', 'Healthcare', 'Finance', 'Consumer']
    sizes = [45, 20, 25, 10]
    colors_pie = ['#00BFFF', '#000080', '#4B0082', '#ADD8E6']
    
    fig_pie, ax_pie = plt.subplots(figsize=(3.5, 3.5))
    wedges, texts, autotexts = ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.75, colors=colors_pie, textprops=dict(color="black"))
    ax_pie.axis('equal')  
    plt.setp(autotexts, size=8, weight="bold", color="white")
    plt.setp(texts, size=8)
    
    buf_pie = io.BytesIO()
    plt.savefig(buf_pie, format='png', dpi=200, bbox_inches='tight', transparent=True)
    buf_pie.seek(0)
    
    t_pie_header = Table([[Paragraph("SECTOR EXPOSURE (Est.)", style_h2)]], colWidths=[190*mm])
    t_pie_header.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER')]))
    elems.append(t_pie_header)
    elems.append(Image(buf_pie, width=70*mm, height=55*mm, hAlign='CENTER')) 
    plt.close()
    elems.append(Spacer(1, 3*mm))

    # 4. RECENT TRADES
    if not trades.empty:
        elems.append(Paragraph("LATEST EXECUTED TRADES", style_h2))
        last = trades.tail(8)[['Date','Ticker','Type','PnL']]
        trade_d = [["DATE", "TICKER", "ACTION", "PnL ($)"]]
        for _, r in last.iterrows():
            d = str(r['Date'])[:10]
            pnl = r['PnL']
            p_sty = style_green if pnl > 0 else style_red
            trade_d.append([d, r['Ticker'], r['Type'], Paragraph(f"{pnl:+,.2f}", p_sty)])
        
        t_trd = Table(trade_d, colWidths=[40*mm, 30*mm, 30*mm, 40*mm])
        t_trd.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#34495e")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.lightgrey),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTSIZE',(0,0),(-1,-1),9) 
        ]))
        elems.append(t_trd)
        
    elems.append(PageBreak())
    
    # --- PAGE 2+: DETAILS ---
    if not signals: elems.append(Paragraph("No Signals.", style_body))
    
    for s in signals:
        is_call = s['action']=='CALL'
        col = colors.HexColor("#00b894") if is_call else colors.HexColor("#d63031")
        
        # Header
        h_data = [[
            Paragraph(f"<b>{s['ticker']}</b>", ParagraphStyle('H', fontSize=24, textColor=colors.black)),
            Table([[Paragraph(f"<b>{s['grade']}</b>", ParagraphStyle('B', textColor=colors.white, alignment=1))]], 
                  colWidths=[55*mm], style=TableStyle([('BACKGROUND',(0,0),(-1,-1),col),('ALIGN',(0,0),(-1,-1),'CENTER')]))
        ]]
        t_h = Table(h_data, colWidths=[125*mm, 60*mm])
        elems.append(t_h)
        elems.append(Table([['']], colWidths=[190*mm], style=TableStyle([('LINEBELOW',(0,0),(-1,-1),3,col)])))
        elems.append(Spacer(1, 8*mm))
        
        # Metrics
        news_p = min(max((s['news_score']+10)/20,0),1)
        news_col = colors.red if s['news_score'] < 0 else col 
        
        metrics_d = [
            ["AI Confidence:", f"%{s['prob']*100:.0f}", ProgressBar(s['prob'], colors.blue)],
            ["News Score:", f"{s['news_score']:.1f}", ProgressBar(news_p, news_col)],
            ["Implied Vol:", f"{s['iv']:.1f}%", ProgressBar(min(s['iv']/100,1), colors.orange)],
            ["Alpha Score:", "High", ProgressBar(0.9, colors.purple)]
        ]
        t_met = Table(metrics_d, colWidths=[30*mm, 15*mm, 35*mm])
        t_met.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        
        # Ticket
        today = pd.Timestamp.now()
        expiry = (today + pd.Timedelta(days=45)).strftime("%d %b %Y")
        ticket_rows = [
            [Paragraph("<b>TRADE EXECUTION</b>", ParagraphStyle('TT', textColor=colors.white, alignment=1))],
            [f"Contract: {s['ticker']} {s['action']} {int(s['tp'])}"],
            [f"Expiry: {expiry} (45 DTE)"],
            [f"Target: ${s['tp']:.2f}"],
            [f"Stop Loss: ${s['sl']:.2f}"],
            [f"R/R Ratio: 1 : 3.5"],
            [f"Risk: ${s['alloc_usd']:,}"],
            [Paragraph("<i>Greeks: \u0394 0.55 \u0393 0.04</i>", style_body)]
        ]
        t_tick = Table(ticket_rows, colWidths=[75*mm])
        t_tick.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0), colors.HexColor("#2c3e50")),
            ('BACKGROUND',(0,1),(-1,-1), colors.HexColor("#ecf0f1")),
            ('GRID',(0,0),(-1,-1),0.5, colors.white),
            ('PADDING',(0,0),(-1,-1), 5)
        ]))
        
        t_layout = Table([[t_met, t_tick]], colWidths=[90*mm, 95*mm])
        t_layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
        elems.append(t_layout)
        elems.append(Spacer(1, 5*mm))
        
        # Rationale & News
        elems.append(Paragraph("INVESTMENT THESIS", style_h2))
        elems.append(Paragraph(s['rationale'], style_body))
        elems.append(Spacer(1, 5*mm))
        
        elems.append(Paragraph("MARKET DRIVERS (Last 7 Days)", style_h2))
        if s['news_items']:
            ndata = []
            for n in s['news_items']:
                icon = "🟢" if n['is_bullish'] else "🔴"
                st = style_green if n['is_bullish'] else style_red
                txt = f"{icon} <b>{n['title']}</b> (Impact: {n['impact']:.1f})"
                ndata.append([Paragraph(txt, st)])
            t_n = Table(ndata, colWidths=[190*mm])
            t_n.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.lightgrey)]))
            elems.append(t_n)
        
        elems.append(Spacer(1, 8*mm))
        
        # --- BOTTOM PART ---
        elems.append(Paragraph("SCENARIO ANALYSIS & TECHNICAL LEVELS", style_h2))
        
        if is_call:
            bull_bg = colors.HexColor("#d4edda"); bear_bg = colors.HexColor("#f8d7da")
            bull_pnl = f"+${s['alloc_usd']*0.35:.0f}"; bear_pnl = f"-${s['alloc_usd']*0.30:.0f}"
        else:
            bull_bg = colors.HexColor("#f8d7da"); bear_bg = colors.HexColor("#d4edda")
            bull_pnl = f"-${s['alloc_usd']*0.30:.0f}"; bear_pnl = f"+${s['alloc_usd']*0.35:.0f}"
            
        scen_d = [
            ["SCENARIO", "PRICE", "EST. PnL"],
            ["BULLISH (+5%)", f"${s['pivot']*1.05:.2f}", bull_pnl],
            ["BASE CASE (Decay)", f"${s['pivot']:.2f}", f"-${s['alloc_usd']*0.08:.0f}"],
            ["BEARISH (-5%)", f"${s['pivot']*0.95:.2f}", bear_pnl]
        ]
        t_scen = Table(scen_d, colWidths=[55*mm, 25*mm, 25*mm])
        t_scen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#34495e")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BACKGROUND', (0,1), (-1,1), bull_bg),
            ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#f8f9fa")),
            ('BACKGROUND', (0,3), (-1,3), bear_bg),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('ALIGN', (1,0), (-1,-1), 'CENTER')
        ]))
        
        tech_d = [
            ["LEVEL", "PRICE", "TYPE"],
            ["Resist 2", f"${s['pivot']*1.05:.2f}", "Major Res"],
            ["Resist 1", f"${s['pivot']*1.03:.2f}", "Resistance"],
            ["Pivot", f"${s['pivot']:.2f}", "Equilibrium"],
            ["Support 1", f"${s['pivot']*0.97:.2f}", "Support"],
            ["Support 2", f"${s['pivot']*0.95:.2f}", "Major Sup"]
        ]
        t_tech = Table(tech_d, colWidths=[30*mm, 25*mm, 25*mm])
        t_tech.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#34495e")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        
        t_mid_bot = Table([[t_scen, Spacer(10*mm,0), t_tech]])
        t_mid_bot.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')])) 
        elems.append(t_mid_bot)
        
        elems.append(Spacer(1, 8*mm))
        
        elems.append(Paragraph("RISK/REWARD VISUALIZATION", style_h2))
        elems.append(Spacer(1, 5*mm))
        
        spectrum = RiskRewardSpectrum(s['sl'], s['pivot'], s['tp'], s['pivot']) 
        t_spec = Table([[spectrum]], colWidths=[190*mm])
        t_spec.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER')]))
        elems.append(t_spec)
        
        elems.append(PageBreak())
        
    disclaimer_text = """
    DISCLAIMER & LEGAL NOTICE:
    This document is provided for informational purposes only and does not constitute an offer to sell or a solicitation of an offer to buy any securities. 
    The information contained herein is based on data obtained from sources believed to be reliable, but its accuracy and completeness cannot be guaranteed.
    
    Past performance is not necessarily indicative of future results. All investments involve risk, including the loss of principal. 
    The strategies discussed may not be suitable for all investors. 
    
    AXIOM QUANT PARTNERS utilizes proprietary algorithmic models which are subject to market risks and model errors. 
    No representation is made that any account will or is likely to achieve profits or losses similar to those shown.
    """
    elems.append(Spacer(1, 180*mm)) 
    elems.append(Paragraph(disclaimer_text, style_disclaimer))
        
    doc.build(elems, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF Generated: {pdf}")
    
    wb = Workbook()
    ws = wb.active
    if signals:
        ws.append(list(signals[0].keys()))
        for x in signals: ws.append([str(v) for v in x.values()])
    wb.save(xlsx)