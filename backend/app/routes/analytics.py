from flask import Blueprint, jsonify, request
from app.db import query_db
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal

analytics_bp = Blueprint("analytics", __name__)

def parse_decimal(val):
    """Safely cast Decimal or None to float for clean JSON serialization."""
    if val is None:
        return 0.0
    return float(val)

def _get_latest_sales_date():
    """Returns the latest sale date in the database as a datetime.date object, or None if no sales exist."""
    try:
        row = query_db("SELECT MAX(DATE(sale_date)) AS max_date FROM sales;", one=True)
        if not row:
            return None
        if isinstance(row, list):
            row = row[0] if row else None
        if not row or not isinstance(row, dict) or not row.get("max_date"):
            return None
        val = row["max_date"]
        if isinstance(val, str):
            try:
                return datetime.strptime(val.split("T")[0].split(" ")[0], "%Y-%m-%d").date()
            except Exception:
                return None
        elif hasattr(val, "date") and callable(val.date):
            return val.date()
        elif isinstance(val, datetime):
            return val.date()
        return val
    except Exception:
        return None

@analytics_bp.route("/analytics/dashboard", methods=["GET"])
def get_dashboard_kpis():
    """
    Get core operational and financial KPIs for the dashboard and analytics view.
    Calculates live metrics from MySQL relative to the latest available sales date:
    - Latest Day Revenue (revenue for the latest available sales date)
    - 30-Day Revenue (ending on the latest available sales date)
    - 30-Day Gross Profit (SUM(quantity * (unit_price - unit_cost)))
    - 30-Day Total Units Sold
    - 30-Day Total Transactions
    - Inventory Valuation (SUM(current_stock * cost_price))
    - Inventory Health counts (Healthy, Low Stock, Overstocked, Out of Stock)
    """
    try:
        max_sales_date = _get_latest_sales_date()

        if max_sales_date:
            latest_day_str = max_sales_date.strftime("%Y-%m-%d")
            # 1. Latest Day's Revenue & Transactions
            latest_sql = """
                SELECT COALESCE(SUM(total_amount), 0) AS latest_revenue,
                       COUNT(sale_id) AS latest_transactions
                FROM sales
                WHERE DATE(sale_date) = %s
            """
            latest_res = query_db(latest_sql, (latest_day_str,), one=True)
            latest_revenue = parse_decimal(latest_res["latest_revenue"])
            latest_transactions = int(latest_res["latest_transactions"])

            # 2. 30-Day Financial KPIs (Revenue, Gross Profit, Units Sold, Transactions)
            start_date = max_sales_date - timedelta(days=29)
            start_dt_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
            end_dt_str = f"{latest_day_str} 23:59:59"

            last_30d_sql = """
                SELECT 
                    COALESCE(SUM(si.quantity * si.unit_price), 0) AS revenue_30d,
                    COALESCE(SUM(si.quantity * (si.unit_price - si.unit_cost)), 0) AS gross_profit_30d,
                    COALESCE(SUM(si.quantity), 0) AS units_sold_30d,
                    COUNT(DISTINCT s.sale_id) AS transactions_30d
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                WHERE s.sale_date >= %s AND s.sale_date <= %s
            """
            kpi_30d = query_db(last_30d_sql, (start_dt_str, end_dt_str), one=True)
            revenue_30d = parse_decimal(kpi_30d["revenue_30d"])
            gross_profit_30d = parse_decimal(kpi_30d["gross_profit_30d"])
            units_sold_30d = int(kpi_30d["units_sold_30d"] or 0)
            transactions_30d = int(kpi_30d["transactions_30d"] or 0)
            gross_margin_pct_30d = round((gross_profit_30d / revenue_30d * 100), 2) if revenue_30d > 0 else 0.0

            # 4. Count of Slow-Moving Products (>30 days since last sale or <=2 units in window)
            slow_movers_sql = """
                SELECT COUNT(DISTINCT p.product_id) AS slow_moving_count
                FROM products p
                JOIN inventory i ON p.product_id = i.product_id
                LEFT JOIN (
                    SELECT si.product_id, MAX(s.sale_date) AS last_sale_date, SUM(si.quantity) AS recent_units
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.sale_id
                    WHERE s.sale_date >= %s AND s.sale_date <= %s
                    GROUP BY si.product_id
                ) sales_summary ON p.product_id = sales_summary.product_id
                WHERE i.current_stock > 0
                  AND (sales_summary.last_sale_date IS NULL OR sales_summary.recent_units <= 2)
            """
            slow_res = query_db(slow_movers_sql, (start_dt_str, end_dt_str), one=True)
            slow_moving_count = int(slow_res["slow_moving_count"] or 0)
        else:
            latest_day_str = None
            latest_revenue = 0.0
            latest_transactions = 0
            revenue_30d = 0.0
            gross_profit_30d = 0.0
            units_sold_30d = 0
            transactions_30d = 0
            gross_margin_pct_30d = 0.0
            slow_moving_count = 0

        # 3. Inventory Valuation and Stock Health Distribution
        inv_sql = """
            SELECT 
                p.product_id,
                p.cost_price,
                p.selling_price,
                i.current_stock,
                i.min_stock_level,
                i.max_stock_level,
                i.safety_stock
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
        """
        inv_rows = query_db(inv_sql) or []

        total_inventory_value = 0.0
        total_retail_value = 0.0
        low_stock_count = 0
        out_of_stock_count = 0
        overstock_count = 0
        healthy_stock_count = 0

        for row in inv_rows:
            stock = int(row["current_stock"])
            cost = float(row["cost_price"])
            price = float(row["selling_price"])
            safety = int(row["safety_stock"])
            max_st = int(row["max_stock_level"])

            total_inventory_value += stock * cost
            total_retail_value += stock * price

            if stock == 0:
                out_of_stock_count += 1
            elif stock <= safety:
                low_stock_count += 1
            elif stock >= max_st:
                overstock_count += 1
            else:
                healthy_stock_count += 1

        if not max_sales_date:
            slow_moving_count = len([r for r in inv_rows if int(r["current_stock"]) > 0])

        return jsonify({
            "status": "success",
            "data": {
                "financial_kpis": {
                    "latest_day_revenue": round(latest_revenue, 2),
                    "latest_day_transactions": latest_transactions,
                    "latest_sales_date": latest_day_str,
                    "today_revenue": round(latest_revenue, 2),
                    "today_transactions": latest_transactions,
                    "revenue_30d": round(revenue_30d, 2),
                    "gross_profit_30d": round(gross_profit_30d, 2),
                    "gross_margin_pct_30d": gross_margin_pct_30d,
                    "units_sold_30d": units_sold_30d,
                    "transactions_30d": transactions_30d,
                },
                "inventory_kpis": {
                    "total_inventory_value": round(total_inventory_value, 2),
                    "total_retail_value": round(total_retail_value, 2),
                    "total_products": len(inv_rows),
                    "low_stock_count": low_stock_count,
                    "out_of_stock_count": out_of_stock_count,
                    "overstock_count": overstock_count,
                    "healthy_stock_count": healthy_stock_count,
                    "slow_moving_count": slow_moving_count
                },
                "calculation_notes": {
                    "gross_profit_formula": "SUM(quantity * (unit_price - unit_cost)) from historical sale_items",
                    "inventory_valuation_formula": "SUM(current_stock * cost_price)",
                    "date_window": f"30 Days ending on {latest_day_str}" if latest_day_str else "No sales recorded"
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to calculate dashboard analytics: {str(e)}"
        }), 500


@analytics_bp.route("/analytics/sales-trend", methods=["GET"])
def get_sales_trend():
    """
    Get aggregated daily sales trends for a given time window (7, 30, or 90 days).
    Anchors to the latest available sales date in the database.
    Returns daily:
    - date (YYYY-MM-DD)
    - revenue
    - gross_profit
    - units_sold
    - transactions
    Missing days in the range are filled with 0s using Pandas for continuous charting.
    """
    try:
        days = request.args.get("days", 30, type=int)
        if days not in [7, 30, 90]:
            days = 30

        max_sales_date = _get_latest_sales_date()

        if not max_sales_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
            full_date_range = pd.date_range(start=start_date, end=end_date).strftime("%Y-%m-%d")
            trend_data = [
                {
                    "date": d,
                    "revenue": 0.0,
                    "gross_profit": 0.0,
                    "units_sold": 0,
                    "transactions": 0
                }
                for d in full_date_range
            ]
            return jsonify({
                "status": "success",
                "time_range_days": days,
                "reference_date": None,
                "data": trend_data
            }), 200

        end_date = max_sales_date
        start_date = end_date - timedelta(days=days - 1)
        start_dt_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        end_dt_str = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"

        trend_sql = """
            SELECT 
                DATE(s.sale_date) AS sale_date_str,
                COALESCE(SUM(si.quantity * si.unit_price), 0) AS daily_revenue,
                COALESCE(SUM(si.quantity * (si.unit_price - si.unit_cost)), 0) AS daily_profit,
                COALESCE(SUM(si.quantity), 0) AS daily_units,
                COUNT(DISTINCT s.sale_id) AS daily_transactions
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.sale_date >= %s AND s.sale_date <= %s
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_date_str ASC
        """
        rows = query_db(trend_sql, (start_dt_str, end_dt_str))

        # Use Pandas for timeline date alignment and gap filling
        full_date_range = pd.date_range(start=start_date, end=end_date).strftime("%Y-%m-%d")
        df_full = pd.DataFrame({"date": full_date_range})

        if rows:
            df_sales = pd.DataFrame(rows)
            df_sales["date"] = df_sales["sale_date_str"].astype(str)
            df_sales["revenue"] = df_sales["daily_revenue"].astype(float)
            df_sales["gross_profit"] = df_sales["daily_profit"].astype(float)
            df_sales["units_sold"] = df_sales["daily_units"].astype(int)
            df_sales["transactions"] = df_sales["daily_transactions"].astype(int)

            df_merged = pd.merge(df_full, df_sales, on="date", how="left").fillna(0)
        else:
            df_merged = df_full.copy()
            df_merged["revenue"] = 0.0
            df_merged["gross_profit"] = 0.0
            df_merged["units_sold"] = 0
            df_merged["transactions"] = 0

        trend_data = []
        for _, row in df_merged.iterrows():
            trend_data.append({
                "date": row["date"],
                "revenue": round(float(row["revenue"]), 2),
                "gross_profit": round(float(row["gross_profit"]), 2),
                "units_sold": int(row["units_sold"]),
                "transactions": int(row["transactions"])
            })

        return jsonify({
            "status": "success",
            "time_range_days": days,
            "reference_date": end_date.strftime("%Y-%m-%d"),
            "data": trend_data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve sales trends: {str(e)}"
        }), 500


@analytics_bp.route("/analytics/top-products", methods=["GET"])
def get_top_products():
    """
    Returns separate rankings for:
    1. Volume Best-Sellers (ranked by SUM(quantity))
    2. Revenue Leaders (ranked by SUM(quantity * unit_price))
    3. Profit Leaders (ranked by SUM(quantity * (unit_price - unit_cost)))
    
    Query Params:
    - days: Time filter (default 30)
    - limit: Max items to return per list (default 5)
    """
    try:
        days = request.args.get("days", 30, type=int)
        limit = request.args.get("limit", 5, type=int)

        max_sales_date = _get_latest_sales_date()
        if not max_sales_date:
            return jsonify({
                "status": "success",
                "time_range_days": days,
                "data": {
                    "best_sellers": [],
                    "revenue_leaders": [],
                    "profit_leaders": []
                }
            }), 200

        start_date = max_sales_date - timedelta(days=days - 1)
        start_dt_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        end_dt_str = f"{max_sales_date.strftime('%Y-%m-%d')} 23:59:59"

        base_sql = """
            SELECT 
                p.product_id,
                p.name AS product_name,
                p.sku,
                p.category,
                COALESCE(SUM(si.quantity), 0) AS total_units_sold,
                COALESCE(SUM(si.quantity * si.unit_price), 0) AS total_revenue,
                COALESCE(SUM(si.quantity * (si.unit_price - si.unit_cost)), 0) AS gross_profit
            FROM products p
            JOIN sale_items si ON p.product_id = si.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.sale_date >= %s AND s.sale_date <= %s
            GROUP BY p.product_id, p.name, p.sku, p.category
        """
        rows = query_db(base_sql, (start_dt_str, end_dt_str))

        if not rows:
            return jsonify({
                "status": "success",
                "time_range_days": days,
                "data": {
                    "best_sellers": [],
                    "revenue_leaders": [],
                    "profit_leaders": []
                }
            }), 200

        df = pd.DataFrame(rows)
        df["units_sold"] = df["total_units_sold"].astype(int)
        df["revenue"] = df["total_revenue"].astype(float)
        df["gross_profit"] = df["gross_profit"].astype(float)
        df["gross_margin_pct"] = df.apply(
            lambda r: round((r["gross_profit"] / r["revenue"] * 100), 2) if r["revenue"] > 0 else 0.0, 
            axis=1
        )

        # 1. Volume Best-Sellers (Ranked strictly by Units Sold)
        best_sellers_df = df.sort_values(by=["units_sold", "revenue"], ascending=[False, False]).head(limit)
        best_sellers = [
            {
                "product_id": int(r["product_id"]),
                "name": r["product_name"],
                "sku": r["sku"],
                "category": r["category"],
                "units_sold": int(r["units_sold"]),
                "revenue": round(float(r["revenue"]), 2),
                "metric_definition": "Ranked by Total Units Sold (SUM(quantity))"
            }
            for _, r in best_sellers_df.iterrows()
        ]

        # 2. Revenue Leaders (Ranked strictly by Total Revenue)
        revenue_leaders_df = df.sort_values(by=["revenue", "units_sold"], ascending=[False, False]).head(limit)
        revenue_leaders = [
            {
                "product_id": int(r["product_id"]),
                "name": r["product_name"],
                "sku": r["sku"],
                "category": r["category"],
                "revenue": round(float(r["revenue"]), 2),
                "units_sold": int(r["units_sold"]),
                "metric_definition": "Ranked by Total Sales Value (SUM(quantity * unit_price))"
            }
            for _, r in revenue_leaders_df.iterrows()
        ]

        # 3. Profit Leaders (Ranked strictly by Gross Profit)
        profit_leaders_df = df.sort_values(by=["gross_profit", "revenue"], ascending=[False, False]).head(limit)
        profit_leaders = [
            {
                "product_id": int(r["product_id"]),
                "name": r["product_name"],
                "sku": r["sku"],
                "category": r["category"],
                "gross_profit": round(float(r["gross_profit"]), 2),
                "revenue": round(float(r["revenue"]), 2),
                "gross_margin_pct": float(r["gross_margin_pct"]),
                "metric_definition": "Ranked by Gross Profit (SUM(quantity * (unit_price - unit_cost)))"
            }
            for _, r in profit_leaders_df.iterrows()
        ]

        return jsonify({
            "status": "success",
            "time_range_days": days,
            "data": {
                "best_sellers": best_sellers,
                "revenue_leaders": revenue_leaders,
                "profit_leaders": profit_leaders
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve top products: {str(e)}"
        }), 500


@analytics_bp.route("/analytics/slow-movers", methods=["GET"])
def get_slow_movers():
    """
    Identify slow-moving inventory items based on the SmartRetail rule:
    - Active stock item (current_stock > 0)
    - Days Since Last Sale > 30 days OR never sold
    - Low sales velocity in the last 30 days (recent_units_sold <= 2)
    
    Returns holding value (current_stock * cost_price) and days dormant.
    """
    try:
        days_threshold = request.args.get("days_threshold", 30, type=int)

        max_sales_date = _get_latest_sales_date()
        ref_date = max_sales_date or datetime.now().date()
        start_date = ref_date - timedelta(days=days_threshold - 1)
        start_dt_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        end_dt_str = f"{ref_date.strftime('%Y-%m-%d')} 23:59:59"
        ref_date_str = ref_date.strftime("%Y-%m-%d")

        sql = """
            SELECT 
                p.product_id,
                p.name AS product_name,
                p.sku,
                p.category,
                p.cost_price,
                p.selling_price,
                i.current_stock,
                i.safety_stock,
                MAX(s.sale_date) AS last_sale_date,
                DATEDIFF(%s, MAX(s.sale_date)) AS days_since_last_sale,
                COALESCE(SUM(CASE WHEN s.sale_date >= %s AND s.sale_date <= %s THEN si.quantity ELSE 0 END), 0) AS recent_units_sold
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            LEFT JOIN sale_items si ON p.product_id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.sale_id
            WHERE i.current_stock > 0
            GROUP BY p.product_id, p.name, p.sku, p.category, p.cost_price, p.selling_price, i.current_stock, i.safety_stock
            HAVING (last_sale_date IS NULL OR days_since_last_sale > %s OR recent_units_sold <= 2)
            ORDER BY days_since_last_sale DESC, (i.current_stock * p.cost_price) DESC
        """
        rows = query_db(sql, (ref_date_str, start_dt_str, end_dt_str, days_threshold))

        slow_movers = []
        for r in rows:
            stock = int(r["current_stock"])
            cost = float(r["cost_price"])
            last_date = r["last_sale_date"]
            days_dormant = int(r["days_since_last_sale"]) if r["days_since_last_sale"] is not None else 999
            recent_units = int(r["recent_units_sold"] or 0)
            holding_value = round(stock * cost, 2)

            slow_movers.append({
                "product_id": int(r["product_id"]),
                "name": r["product_name"],
                "sku": r["sku"],
                "category": r["category"],
                "current_stock": stock,
                "safety_stock": int(r["safety_stock"]),
                "cost_price": cost,
                "inventory_holding_value": holding_value,
                "last_sale_date": last_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(last_date, "strftime") else (str(last_date) if last_date else None),
                "days_since_last_sale": days_dormant if last_date else None,
                "never_sold": last_date is None,
                "recent_units_sold_30d": recent_units,
                "reason": "Never sold" if last_date is None else f"Inactive for {days_dormant} days with only {recent_units} units sold recently"
            })

        return jsonify({
            "status": "success",
            "threshold_days": days_threshold,
            "total_slow_movers": len(slow_movers),
            "data": slow_movers
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve slow-moving products: {str(e)}"
        }), 500


@analytics_bp.route("/analytics/category-performance", methods=["GET"])
def get_category_performance():
    """
    Calculate performance aggregated by product category:
    - units_sold
    - revenue
    - gross_profit
    - gross_margin_pct
    - product_count
    """
    try:
        days = request.args.get("days", 30, type=int)

        max_sales_date = _get_latest_sales_date()
        if max_sales_date:
            start_date = max_sales_date - timedelta(days=days - 1)
            start_dt_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
            end_dt_str = f"{max_sales_date.strftime('%Y-%m-%d')} 23:59:59"

            sql = """
                SELECT 
                    p.category,
                    COUNT(DISTINCT p.product_id) AS product_count,
                    COALESCE(SUM(si.quantity), 0) AS units_sold,
                    COALESCE(SUM(si.quantity * si.unit_price), 0) AS category_revenue,
                    COALESCE(SUM(si.quantity * (si.unit_price - si.unit_cost)), 0) AS category_profit
                FROM products p
                LEFT JOIN sale_items si ON p.product_id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.sale_id AND s.sale_date >= %s AND s.sale_date <= %s
                GROUP BY p.category
                ORDER BY category_revenue DESC
            """
            rows = query_db(sql, (start_dt_str, end_dt_str))
        else:
            sql = """
                SELECT 
                    p.category,
                    COUNT(DISTINCT p.product_id) AS product_count,
                    0 AS units_sold,
                    0 AS category_revenue,
                    0 AS category_profit
                FROM products p
                GROUP BY p.category
            """
            rows = query_db(sql)

        categories = []
        for r in rows:
            rev = parse_decimal(r["category_revenue"])
            profit = parse_decimal(r["category_profit"])
            margin = round((profit / rev * 100), 2) if rev > 0 else 0.0

            categories.append({
                "category": r["category"],
                "product_count": int(r["product_count"]),
                "units_sold": int(r["units_sold"] or 0),
                "revenue": round(rev, 2),
                "gross_profit": round(profit, 2),
                "gross_margin_pct": margin
            })

        return jsonify({
            "status": "success",
            "time_range_days": days,
            "data": categories
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve category performance: {str(e)}"
        }), 500
