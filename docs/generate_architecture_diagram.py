import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram(output_path):
    W, H = 1600, 2450
    img = Image.new("RGB", (W, H), color="#0B1120")
    draw = ImageDraw.Draw(img)

    # Load system fonts with fallback
    def get_font(size, bold=False):
        font_names = [
            "segoeuib.ttf" if bold else "segoeui.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        ]
        for name in font_names:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    font_title = get_font(36, bold=True)
    font_subtitle = get_font(18, bold=False)
    font_sec_title = get_font(22, bold=True)
    font_card_title = get_font(18, bold=True)
    font_body = get_font(16, bold=False)
    font_body_bold = get_font(16, bold=True)
    font_code = get_font(14, bold=False)
    font_badge = get_font(13, bold=True)

    # Subtle background dots
    for x in range(0, W, 40):
        for y in range(0, H, 40):
            draw.point((x, y), fill="#1E293B")

    # Helper function for drawing rounded rectangles with shadow
    def draw_card(box, bg_color, border_color, border_width=2, radius=12):
        x0, y0, x1, y1 = box
        draw.rounded_rectangle([x0+4, y0+4, x1+4, y1+4], radius=radius, fill="#050B14")
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bg_color, outline=border_color, width=border_width)

    # Helper function for vertical connector arrow
    def draw_down_arrow(x, y0, y1, text="", color="#64748B"):
        draw.line([(x, y0), (x, y1)], fill=color, width=3)
        draw.polygon([(x - 7, y1 - 10), (x + 7, y1 - 10), (x, y1)], fill=color)
        if text:
            bbox = font_badge.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            my = (y0 + y1) // 2
            draw.rounded_rectangle([x - tw//2 - 10, my - th//2 - 5, x + tw//2 + 10, my + th//2 + 5], radius=6, fill="#0F172A", outline="#334155", width=1)
            draw.text((x - tw//2, my - th//2 - 2), text, font=font_badge, fill="#94A3B8")

    # Helper for category tag pill
    def draw_tag(x, y, text, bg_color, text_color):
        bbox = font_badge.getbbox(text)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([x, y, x + tw + 16, y + 26], radius=6, fill=bg_color)
        draw.text((x + 8, y + 4), text, font=font_badge, fill=text_color)
        return x + tw + 24

    # --- 1. HEADER SECTION ---
    draw_card((50, 40, W - 50, 150), "#0F172A", "#38BDF8", border_width=2, radius=16)
    draw_tag(75, 56, "ARCHITECTURE", "#0369A1", "#BAE6FD")
    draw.text((215, 52), "SmartRetail — End-to-End System Architecture & Decision Flow", font=font_title, fill="#F8FAFC")
    draw.text((75, 104), "Real-time POS Sales Analytics • ML Demand Forecasting • Explainable Human-in-the-Loop Reorders", font=font_subtitle, fill="#94A3B8")
    
    # Header badge
    draw.rounded_rectangle([W - 240, 72, W - 75, 114], radius=8, fill="#1E293B", outline="#10B981", width=1)
    draw.text((W - 222, 83), "PROD DEPLOYED", font=font_badge, fill="#10B981")

    # --- 2. USER LAYER ---
    curr_y = 185
    draw_card((50, curr_y, W - 50, curr_y + 115), "#131E33", "#38BDF8", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 1", "#0369A1", "#BAE6FD")
    draw.text((165, curr_y + 18), "USER / STORE OPERATOR LAYER (Human-in-the-Loop Decision Maker)", font=font_sec_title, fill="#38BDF8")
    draw.text((80, curr_y + 58), "• Store Owner & Cashier Access   • Dedicated Role Authentication   • Evaluates Explainable Reorder Advice", font=font_body, fill="#CBD5E1")
    draw.text((80, curr_y + 82), "• Retains Full Authority over Actual Supplier Purchasing Decisions (Zero Automated Orders Placed)", font=font_body_bold, fill="#F59E0B")

    draw_down_arrow(W // 2, curr_y + 115, curr_y + 160, "HTTPS Browser Interaction", "#38BDF8")

    # --- 3. FRONTEND LAYER (Vercel) ---
    curr_y = 345
    draw_card((50, curr_y, W - 50, curr_y + 265), "#0F172A", "#3B82F6", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 2", "#1D4ED8", "#BFDBFE")
    draw.text((165, curr_y + 18), "REACT 18 + VITE FRONTEND LAYER (Hosted on Vercel)", font=font_sec_title, fill="#60A5FA")
    draw.text((80, curr_y + 52), "Single Page Application (SPA) with centralized REST client, responsive CSS design tokens & Chart.js visualizations", font=font_body, fill="#94A3B8")

    modules = [
        ("Authentication", "Store Owner login session"),
        ("Dashboard", "Latest Day Revenue & KPIs"),
        ("Inventory", "Catalog & stock levels"),
        ("POS Sales", "Multi-item receipts & checkout"),
        ("Retail Analytics", "30-Day trends, profit margins"),
        ("Demand Forecast", "7D & 30D horizon curves"),
        ("Intelligence", "Stockout & overstock badges"),
        ("Monitoring", "MAE, RMSE & drift tracking")
    ]
    card_w = (W - 100 - 30 * 3) // 4
    for i, (m_title, m_desc) in enumerate(modules):
        r, c = i // 4, i % 4
        mx = 75 + c * (card_w + 10)
        my = curr_y + 85 + r * 80
        draw_card((mx, my, mx + card_w, my + 70), "#1E293B", "#334155", border_width=1, radius=8)
        draw.text((mx + 12, my + 10), m_title, font=font_card_title, fill="#F1F5F9")
        draw.text((mx + 12, my + 38), m_desc, font=font_code, fill="#94A3B8")

    draw_down_arrow(W // 2, curr_y + 265, curr_y + 310, "Secure REST API Calls (/api/...)", "#3B82F6")

    # --- 4. BACKEND API LAYER (Render) ---
    curr_y = 655
    draw_card((50, curr_y, W - 50, curr_y + 265), "#0F172A", "#10B981", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 3", "#047857", "#A7F3D0")
    draw.text((165, curr_y + 18), "FLASK 3.0 REST API BACKEND (Hosted on Render via Gunicorn)", font=font_sec_title, fill="#34D399")
    draw.text((80, curr_y + 52), "Python 3.10+ WSGI server, modular blueprints, CORS protection, parameterization & error handlers", font=font_body, fill="#94A3B8")

    api_endpoints = [
        ("POST /api/auth/login", "Password hash verification"),
        ("GET /api/products", "Catalog CRUD & SKU validation"),
        ("GET /api/inventory", "Stock master & lead-time levels"),
        ("POST /api/sales", "Atomic POS sales deduction"),
        ("GET /api/analytics", "Dashboard KPIs & 30D sales trend"),
        ("POST /api/forecast", "Multi-step demand prediction"),
        ("GET /api/intelligence", "Explainable reorder advice"),
        ("GET /api/monitoring", "Historical accuracy & metrics")
    ]
    for i, (ep_name, ep_desc) in enumerate(api_endpoints):
        r, c = i // 4, i % 4
        mx = 75 + c * (card_w + 10)
        my = curr_y + 85 + r * 80
        draw_card((mx, my, mx + card_w, my + 70), "#1E293B", "#1E3A8A", border_width=1, radius=8)
        draw.text((mx + 12, my + 10), ep_name, font=font_card_title, fill="#38BDF8")
        draw.text((mx + 12, my + 38), ep_desc, font=font_code, fill="#94A3B8")

    draw_down_arrow(W // 2, curr_y + 265, curr_y + 310, "Thread-Safe TLS / SSL SQL Queries", "#10B981")

    # --- 5. DATABASE LAYER (TiDB Cloud) ---
    curr_y = 965
    draw_card((50, curr_y, W - 50, curr_y + 245), "#0F172A", "#F59E0B", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 4", "#B45309", "#FDE68A")
    draw.text((165, curr_y + 18), "MANAGED RELATIONAL DATABASE (TiDB Cloud — MySQL 8.0 Compatible)", font=font_sec_title, fill="#FBBF24")
    draw.text((80, curr_y + 52), "9 Normalized Relational Tables • ACID Atomic Transactions • Foreign Key Cascades & Referential Integrity", font=font_body, fill="#94A3B8")

    tables = [
        ("stores", "Store profile & currency"),
        ("users", "Store Owner credentials"),
        ("suppliers", "Supplier directory & lead time"),
        ("products", "20 FreshRetailNet SKUs"),
        ("inventory", "Stock, safety, min/max"),
        ("sales", "97 Daily POS receipts"),
        ("sale_items", "1,910 Line item records"),
        ("forecasts", "Stored horizon predictions"),
        ("reorder_recommendations", "Explainable reorder audit")
    ]
    t_card_w = (W - 100 - 20 * 2) // 3
    for i, (tbl_name, tbl_desc) in enumerate(tables):
        r, c = i // 3, i % 3
        tx = 75 + c * (t_card_w + 10)
        ty = curr_y + 85 + r * 46
        draw.rounded_rectangle([tx, ty, tx + t_card_w, ty + 38], radius=6, fill="#1E293B", outline="#475569", width=1)
        draw.text((tx + 12, ty + 9), tbl_name, font=font_body_bold, fill="#FDE68A")
        
        # Calculate offset for description
        desc_x = tx + 240 if len(tbl_name) > 15 else tx + 130
        draw.text((desc_x, ty + 9), f"—  {tbl_desc}", font=font_code, fill="#CBD5E1")

    draw_down_arrow(W // 2, curr_y + 245, curr_y + 290, "Historical Sales & Stock Master Pipeline", "#F59E0B")

    # --- 6. DATA PROCESSING & ML FORECASTING ENGINE ---
    curr_y = 1255
    draw_card((50, curr_y, W - 50, curr_y + 355), "#0F172A", "#8B5CF6", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 5", "#6D28D9", "#DDD6FE")
    draw.text((165, curr_y + 18), "DATA PROCESSING & ML FORECASTING ENGINE (Pandas, NumPy, Scikit-Learn)", font=font_sec_title, fill="#A78BFA")
    draw.text((80, curr_y + 52), "Time-series aggregation, stockout-aware latent demand cleaning, temporal validation & recursive multi-step forecasting", font=font_body, fill="#94A3B8")

    box_w = (W - 100 - 30 * 3) // 4
    ml_steps = [
        ("1. Daily Sales Grid", "• 1,940 Store 18 records\n• Infill missing zero days\n• Stockout latent correction", "#1E293B", "#4C1D95"),
        ("2. Feature Engineering", "• Lags: 1, 7, 14, 28 days\n• 7D/14D/30D Rolling Stats\n• Day-of-Week & Weekend", "#1E293B", "#4C1D95"),
        ("3. Model Benchmarking", "• Naive Baseline\n• Ridge & Gradient Boosting\n• Random Forest Regressor", "#1E293B", "#4C1D95"),
        ("4. Selected Production Model", "• 7-Day Moving Average\n• Selected Baseline Model\n• 7D & 30D Horizon Output", "#2E1065", "#A78BFA")
    ]
    for i, (st_title, st_desc, bg_c, brd_c) in enumerate(ml_steps):
        bx = 75 + i * (box_w + 10)
        by = curr_y + 85
        draw_card((bx, by, bx + box_w, by + 145), bg_c, brd_c, border_width=2 if i==3 else 1, radius=10)
        draw.text((bx + 12, by + 12), st_title, font=font_card_title, fill="#F5F3FF")
        for line_idx, line in enumerate(st_desc.split("\n")):
            draw.text((bx + 12, by + 45 + line_idx * 24), line, font=font_code, fill="#E9D5FF" if i==3 else "#CBD5E1")

    # Evaluation Note Bar
    draw.rounded_rectangle([75, curr_y + 250, W - 75, curr_y + 330], radius=8, fill="#18182E", outline="#7C3AED", width=1)
    draw.text((95, curr_y + 263), "Model Evaluation Note:", font=font_body_bold, fill="#C4B5FD")
    draw.text((95, curr_y + 293), "Multiple algorithms were evaluated under chronological validation. The 7-Day Moving Average was selected for production stability without unnecessary algorithmic complexity.", font=font_body, fill="#E2E8F0")

    draw_down_arrow(W // 2, curr_y + 355, curr_y + 400, "Forecast Demand Curves (7D & 30D)", "#8B5CF6")

    # --- 7. INVENTORY INTELLIGENCE & EXPLAINABLE REORDER ENGINE ---
    curr_y = 1655
    draw_card((50, curr_y, W - 50, curr_y + 330), "#0F172A", "#EC4899", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 6", "#BE185D", "#FBCFE8")
    draw.text((165, curr_y + 18), "INVENTORY INTELLIGENCE & EXPLAINABLE DECISION ENGINE", font=font_sec_title, fill="#F472B6")
    draw.text((80, curr_y + 52), "Converts machine learning demand predictions into transparent, mathematically rigorous inventory guidance", font=font_body, fill="#94A3B8")

    col_w = (W - 100 - 30 * 2) // 3
    cy = curr_y + 85

    # Col 1
    cx1 = 75
    draw_card((cx1, cy, cx1 + col_w, cy + 225), "#1E293B", "#DB2777", border_width=1, radius=10)
    draw.text((cx1 + 16, cy + 16), "Stock Risk Detection", font=font_card_title, fill="#FDF2F8")
    draw.text((cx1 + 16, cy + 50), "• Stockout Risk Trigger:", font=font_body_bold, fill="#F43F5E")
    draw.text((cx1 + 16, cy + 74), "  Stock < Lead Demand + Safety", font=font_code, fill="#CBD5E1")
    draw.text((cx1 + 16, cy + 110), "• Overstock Risk Trigger:", font=font_body_bold, fill="#F59E0B")
    draw.text((cx1 + 16, cy + 134), "  Stock > 1.5 × 30-Day Velocity", font=font_code, fill="#CBD5E1")
    draw.text((cx1 + 16, cy + 170), "• Dynamic Safety Stock Buffer:", font=font_body_bold, fill="#38BDF8")
    draw.text((cx1 + 16, cy + 194), "  Z × σ(daily demand) × √L", font=font_code, fill="#CBD5E1")

    # Col 2
    cx2 = 75 + col_w + 15
    draw_card((cx2, cy, cx2 + col_w, cy + 225), "#1E293B", "#DB2777", border_width=1, radius=10)
    draw.text((cx2 + 16, cy + 16), "Mathematical Reorder Logic", font=font_card_title, fill="#FDF2F8")
    draw.text((cx2 + 16, cy + 50), "1. Required Stock Formula:", font=font_body_bold, fill="#F472B6")
    draw.text((cx2 + 16, cy + 74), "   Required = Forecast + Safety", font=font_code, fill="#CBD5E1")
    draw.text((cx2 + 16, cy + 110), "2. Recommended Reorder Formula:", font=font_body_bold, fill="#F472B6")
    draw.text((cx2 + 16, cy + 134), "   Reorder = max(0, Required", font=font_code, fill="#CBD5E1")
    draw.text((cx2 + 16, cy + 156), "   - Current Stock - On Order)", font=font_code, fill="#CBD5E1")
    draw.text((cx2 + 16, cy + 190), "• Stock on Order = 0 (MVP Boundary)", font=font_badge, fill="#94A3B8")

    # Col 3
    cx3 = 75 + (col_w + 15) * 2
    draw_card((cx3, cy, cx3 + col_w, cy + 225), "#1E293B", "#DB2777", border_width=1, radius=10)
    draw.text((cx3 + 16, cy + 16), "Transparent Explainability", font=font_card_title, fill="#FDF2F8")
    draw.text((cx3 + 16, cy + 50), "• 'Why Reorder?' Modal:", font=font_body_bold, fill="#34D399")
    draw.text((cx3 + 16, cy + 74), "  Full step-by-step arithmetic", font=font_code, fill="#CBD5E1")
    draw.text((cx3 + 16, cy + 110), "• Input Parameter Audit Trail:", font=font_body_bold, fill="#34D399")
    draw.text((cx3 + 16, cy + 134), "  Lead days, velocity & safety", font=font_code, fill="#CBD5E1")
    draw.text((cx3 + 16, cy + 170), "• Decision-Support Protocol:", font=font_body_bold, fill="#FBBF24")
    draw.text((cx3 + 16, cy + 194), "  Actionable advice for owner", font=font_code, fill="#CBD5E1")

    draw_down_arrow(W // 2, curr_y + 330, curr_y + 375, "Actionable Decision-Support Outputs", "#EC4899")

    # --- 8. DECISION SUPPORT & GOVERNANCE LAYER ---
    curr_y = 2030
    draw_card((50, curr_y, W - 50, curr_y + 175), "#111827", "#EF4444", border_width=2, radius=14)
    draw_tag(80, curr_y + 18, "LAYER 7", "#991B1B", "#FCA5A5")
    draw.text((165, curr_y + 18), "EXECUTIVE DECISION SUPPORT & GOVERNANCE PROTOCOL", font=font_sec_title, fill="#F87171")
    draw.text((80, curr_y + 55), "• Latest Day Revenue & Financial KPIs (₹1,069,725 total revenue across 97 sales days)", font=font_body, fill="#E2E8F0")
    draw.text((80, curr_y + 80), "• Category Profitability Analysis & Slow-Moving Stock Capital Valuation", font=font_body, fill="#E2E8F0")
    draw.text((80, curr_y + 105), "• Reorder Recommendations with Full Mathematical Justification", font=font_body, fill="#E2E8F0")

    # Red Guardrail Banner
    guard_x = W - 580
    draw.rounded_rectangle([guard_x, curr_y + 20, W - 80, curr_y + 155], radius=10, fill="#7F1D1D", outline="#EF4444", width=2)
    draw.text((guard_x + 20, curr_y + 35), "STRICT GOVERNANCE RULE", font=font_card_title, fill="#FECACA")
    draw.text((guard_x + 20, curr_y + 68), "• NO AUTOMATIC ORDER PLACEMENT", font=font_body_bold, fill="#FFFFFF")
    draw.text((guard_x + 20, curr_y + 94), "• 100% HUMAN-IN-THE-LOOP APPROVAL", font=font_body_bold, fill="#FDE047")
    draw.text((guard_x + 20, curr_y + 120), "• Store owner makes final decision", font=font_code, fill="#FCA5A5")

    # --- 9. DEPLOYMENT FOOTER BANNER ---
    curr_y = 2235
    draw_card((50, curr_y, W - 50, curr_y + 150), "#0F172A", "#64748B", border_width=1, radius=12)
    draw_tag(80, curr_y + 16, "CLOUD TOPOLOGY", "#334155", "#E2E8F0")
    draw.text((230, curr_y + 16), "LIVE CLOUD PRODUCTION DEPLOYMENT ARCHITECTURE", font=font_card_title, fill="#94A3B8")
    
    dep_w = (W - 100 - 30 * 2) // 3
    # Vercel
    dx1 = 75
    draw.rounded_rectangle([dx1, curr_y + 52, dx1 + dep_w, curr_y + 130], radius=8, fill="#1E293B", outline="#3B82F6", width=1)
    draw.text((dx1 + 14, curr_y + 64), "Frontend : Vercel", font=font_body_bold, fill="#60A5FA")
    draw.text((dx1 + 14, curr_y + 92), "https://smart-retail-eta.vercel.app", font=font_code, fill="#94A3B8")

    # Render
    dx2 = 75 + dep_w + 15
    draw.rounded_rectangle([dx2, curr_y + 52, dx2 + dep_w, curr_y + 130], radius=8, fill="#1E293B", outline="#10B981", width=1)
    draw.text((dx2 + 14, curr_y + 64), "Backend : Render (Gunicorn)", font=font_body_bold, fill="#34D399")
    draw.text((dx2 + 14, curr_y + 92), "https://smartretail-backend-12n4.onrender.com", font=font_code, fill="#94A3B8")

    # TiDB Cloud
    dx3 = 75 + (dep_w + 15) * 2
    draw.rounded_rectangle([dx3, curr_y + 52, dx3 + dep_w, curr_y + 130], radius=8, fill="#1E293B", outline="#F59E0B", width=1)
    draw.text((dx3 + 14, curr_y + 64), "Database : TiDB Cloud", font=font_body_bold, fill="#FBBF24")
    draw.text((dx3 + 14, curr_y + 92), "gateway01.ap-northeast-1 (TLS/SSL)", font=font_code, fill="#94A3B8")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    print(f"Architecture diagram successfully generated at: {output_path}")

if __name__ == "__main__":
    out = os.path.join("docs", "smartretail-system-architecture.png")
    create_architecture_diagram(out)
