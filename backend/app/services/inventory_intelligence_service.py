import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.db import query_db, get_db, execute_db
from app.services.forecast_service import generate_and_save_forecast, get_stored_forecasts

# Configurable Service-Level Parameters
Z_SERVICE_LEVEL = 1.65            # ~95% cycle service level
OVERSTOCK_THRESHOLD_FACTOR = 1.5  # 1.5x of 30-day demand
STOCK_ON_ORDER_MVP = 0            # MVP Assumption: No PO workflow active

def calculate_volatility_safety_stock(product_id, lead_time_days, z_value=Z_SERVICE_LEVEL):
    """
    Calculates statistical safety stock from historical daily sales volatility:
    Safety Stock = ceil(Z * std_dev(daily_demand) * sqrt(lead_time_days))
    Returns safety stock integer, standard deviation, and boolean flag.
    """
    sales_sql = """
        SELECT 
            DATE(s.sale_date) AS sale_date_str,
            COALESCE(SUM(si.quantity), 0) AS daily_qty
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE si.product_id = %s
        GROUP BY DATE(s.sale_date)
    """
    rows = query_db(sales_sql, (product_id,))
    if not rows or len(rows) < 2:
        return 0, 0.0, False

    daily_values = [float(r["daily_qty"]) for r in rows]
    std_dev = float(np.std(daily_values, ddof=1))
    
    if std_dev == 0 or lead_time_days <= 0:
        return 0, 0.0, True

    calculated_ss = math.ceil(z_value * std_dev * math.sqrt(lead_time_days))
    return int(calculated_ss), round(std_dev, 2), True


def calculate_product_inventory_intelligence(product_id, horizon_days=7):
    """
    Computes comprehensive inventory intelligence and deterministic explainability for a product:
    - Current stock & lead time
    - Safety stock (configured or dynamic volatility fallback)
    - Stored forecast demand & lead-time demand
    - Stockout risk & stockout gap
    - Overstock risk & 30-day velocity threshold
    - Recommended reorder quantity & status
    - Structured 'explanation' block explaining the WHY behind every metric
    """
    if horizon_days not in [7, 30]:
        raise ValueError("Planning horizon must be either 7 or 30 days.")

    # 1. Retrieve Product and Inventory Details
    sql = """
        SELECT 
            p.product_id,
            p.sku,
            p.name AS product_name,
            p.category,
            p.cost_price,
            p.selling_price,
            i.current_stock,
            i.min_stock_level,
            i.max_stock_level,
            i.safety_stock AS configured_safety_stock,
            i.lead_time_days
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = %s
    """
    item = query_db(sql, (product_id,), one=True)
    if not item:
        raise ValueError(f"Product ID {product_id} with inventory record not found.")

    current_stock = int(item["current_stock"])
    lead_time_days = int(item["lead_time_days"]) if item["lead_time_days"] else 3
    configured_ss = int(item["configured_safety_stock"]) if item["configured_safety_stock"] is not None else 0

    # 2. Safety Stock Resolution
    std_dev = None
    if configured_ss > 0:
        safety_stock = configured_ss
        ss_source = "configured_inventory_safety_stock"
    else:
        calc_ss, std_dev, estimated = calculate_volatility_safety_stock(product_id, lead_time_days)
        safety_stock = calc_ss
        ss_source = "dynamic_volatility_fallback" if estimated else "zero_insufficient_history"

    # 3. Retrieve or Generate Stored Forecast
    forecast_sql = """
        SELECT target_date, predicted_demand
        FROM forecasts
        WHERE product_id = %s AND horizon_days = %s
        ORDER BY forecast_date DESC, target_date ASC
        LIMIT %s
    """
    forecast_rows = query_db(forecast_sql, (product_id, horizon_days, horizon_days))
    
    if not forecast_rows or len(forecast_rows) < horizon_days:
        # Generate on the fly using ML pipeline
        try:
            gen_res = generate_and_save_forecast(product_id, horizon_days)
            forecast_rows = gen_res["predictions"]
        except Exception:
            forecast_rows = []

    if forecast_rows:
        predictions = [float(r["predicted_demand"]) for r in forecast_rows]
        forecasted_demand = round(sum(predictions), 2)
        avg_daily_forecast = round(forecasted_demand / len(predictions), 2)
        
        # Lead-time demand: sum of predictions within lead time window
        if lead_time_days <= len(predictions):
            lead_time_demand = round(sum(predictions[:lead_time_days]), 2)
            lead_time_extrapolated = False
        else:
            # Proportional extrapolation if lead time exceeds stored forecast horizon
            lead_time_demand = round(avg_daily_forecast * lead_time_days, 2)
            lead_time_extrapolated = True
    else:
        forecasted_demand = 0.0
        avg_daily_forecast = 0.0
        lead_time_demand = 0.0
        lead_time_extrapolated = False

    # 4. Stockout Risk Logic
    risk_stock_required = round(lead_time_demand + safety_stock, 2)
    stockout_risk = current_stock < risk_stock_required
    stockout_gap = max(0.0, round(risk_stock_required - current_stock, 2))

    # 5. Overstock Risk Logic
    sales_30d_sql = """
        SELECT COALESCE(SUM(si.quantity), 0) AS units_30d
        FROM sales s
        JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE si.product_id = %s AND s.sale_date >= NOW() - INTERVAL 30 DAY
    """
    sales_30d_res = query_db(sales_30d_sql, (product_id,), one=True)
    units_30d = int(sales_30d_res["units_30d"] or 0)
    avg_30d_demand = round(units_30d / 30.0, 2)
    overstock_threshold = round(units_30d * OVERSTOCK_THRESHOLD_FACTOR, 2)

    if units_30d > 0:
        overstock_risk = current_stock > overstock_threshold
        overstock_note = "Stock exceeds 1.5x of 30-day demand" if overstock_risk else "Stock within healthy bounds"
    else:
        max_stock = int(item["max_stock_level"]) if item["max_stock_level"] else 100
        overstock_risk = current_stock >= max_stock
        overstock_note = "Zero sales in last 30 days with stock at/above maximum capacity" if overstock_risk else "No recent sales (dormant)"

    # 6. Reorder Recommendation Calculation
    required_stock = round(forecasted_demand + safety_stock, 2)
    raw_reorder = required_stock - current_stock - STOCK_ON_ORDER_MVP
    recommended_quantity = int(math.ceil(max(0.0, raw_reorder)))
    recommendation_status = "REORDER" if recommended_quantity > 0 else "NO_REORDER"

    calculation_date = datetime.now().strftime("%Y-%m-%d")

    # 7. Structured Deterministic Explainability Payload
    if recommended_quantity > 0:
        reorder_reason = (
            f"Expected demand ({forecasted_demand} units over {horizon_days} days) plus safety stock "
            f"({safety_stock} units) is higher than current available stock ({current_stock} units)."
        )
    else:
        reorder_reason = (
            f"Current stock ({current_stock} units) is sufficient to cover expected {horizon_days}-day demand "
            f"({forecasted_demand} units) and the safety stock buffer ({safety_stock} units)."
        )

    if stockout_risk:
        stockout_reason = (
            f"Stockout risk is detected because current stock ({current_stock} units) is below expected demand "
            f"during supplier lead time ({lead_time_demand} units over {lead_time_days} days) plus safety stock ({safety_stock} units)."
        )
    else:
        stockout_reason = (
            f"Current stock ({current_stock} units) covers expected lead-time demand ({lead_time_demand} units) "
            f"and safety stock ({safety_stock} units)."
        )

    if overstock_risk:
        overstock_reason = (
            f"Current stock ({current_stock} units) is above the configured overstock threshold ({overstock_threshold} units) "
            f"based on recent 30-day demand ({units_30d} units sold, avg {avg_30d_demand} units/day)."
        )
    else:
        overstock_reason = (
            f"Current stock ({current_stock} units) is within healthy demand thresholds (threshold: {overstock_threshold} units)."
        )

    if ss_source == "configured_inventory_safety_stock":
        safety_stock_reason = "Safety stock is configured for this product in the inventory master."
    elif ss_source == "dynamic_volatility_fallback":
        safety_stock_reason = (
            f"Safety stock provides an additional buffer against variation in daily demand during the supplier lead time "
            f"(sigma={std_dev}, Z={Z_SERVICE_LEVEL}, lead_time={lead_time_days} days)."
        )
    else:
        safety_stock_reason = "Safety stock could not be statistically estimated because there is insufficient historical demand data."

    explanation = {
        "reorder": {
            "recommended": recommended_quantity > 0,
            "recommended_quantity": recommended_quantity,
            "required_stock": required_stock,
            "forecasted_demand": forecasted_demand,
            "planning_horizon_days": horizon_days,
            "safety_stock": safety_stock,
            "current_stock": current_stock,
            "stock_on_order": STOCK_ON_ORDER_MVP,
            "formula": "Required Stock (Forecasted Demand + Safety Stock) - Current Stock - Stock on Order",
            "calculation_string": f"({forecasted_demand} + {safety_stock}) - {current_stock} - {STOCK_ON_ORDER_MVP} = {raw_reorder:.2f} -> {recommended_quantity} units",
            "reason": reorder_reason,
            "mvp_assumption": "Purchase order tracking is not implemented in MVP (stock_on_order = 0)."
        },
        "stockout_risk": {
            "risk_detected": stockout_risk,
            "current_stock": current_stock,
            "lead_time_days": lead_time_days,
            "lead_time_demand": lead_time_demand,
            "safety_stock": safety_stock,
            "lead_time_required_stock": risk_stock_required,
            "stockout_gap": stockout_gap,
            "formula": "Lead-Time Demand + Safety Stock > Current Stock",
            "calculation_string": f"Lead-Time Demand ({lead_time_demand}) + Safety ({safety_stock}) = {risk_stock_required} vs Current Stock ({current_stock})",
            "reason": stockout_reason
        },
        "overstock_risk": {
            "risk_detected": overstock_risk,
            "current_stock": current_stock,
            "units_sold_30d": units_30d,
            "average_30_day_demand": avg_30d_demand,
            "overstock_threshold_factor": OVERSTOCK_THRESHOLD_FACTOR,
            "overstock_threshold": overstock_threshold,
            "excess_units": max(0, int(round(current_stock - overstock_threshold))),
            "formula": "Current Stock > Total 30D Sales * Threshold Factor (1.5x)",
            "calculation_string": f"Current Stock ({current_stock}) vs Threshold ({overstock_threshold:.2f} units)",
            "reason": overstock_reason
        },
        "safety_stock": {
            "safety_stock": safety_stock,
            "source": ss_source,
            "z_value": Z_SERVICE_LEVEL,
            "demand_std_dev": std_dev,
            "lead_time_days": lead_time_days,
            "formula": "Z * StdDev(Daily Demand) * sqrt(Lead Time Days)",
            "reason": safety_stock_reason
        },
        "decision_protocol": {
            "human_in_the_loop": True,
            "statement": "SmartRetail is a decision-support platform. The store owner always makes the final purchasing decision. No automated orders are placed."
        }
    }

    return {
        "product_id": item["product_id"],
        "sku": item["sku"],
        "name": item["product_name"],
        "category": item["category"],
        "cost_price": float(item["cost_price"]),
        "selling_price": float(item["selling_price"]),
        "current_stock": current_stock,
        "lead_time_days": lead_time_days,
        "safety_stock": safety_stock,
        "safety_stock_source": ss_source,
        "lead_time_demand": lead_time_demand,
        "lead_time_extrapolated": lead_time_extrapolated,
        "planning_horizon_days": horizon_days,
        "forecasted_demand": forecasted_demand,
        "required_stock": required_stock,
        "stockout_risk": stockout_risk,
        "stockout_gap": stockout_gap,
        "risk_stock_required": risk_stock_required,
        "units_sold_30d": units_30d,
        "average_30_day_demand": avg_30d_demand,
        "overstock_threshold": overstock_threshold,
        "overstock_risk": overstock_risk,
        "overstock_note": overstock_note,
        "stock_on_order": STOCK_ON_ORDER_MVP,
        "recommended_quantity": recommended_quantity,
        "recommendation_status": recommendation_status,
        "calculation_date": calculation_date,
        "explanation": explanation
    }


def persist_reorder_recommendation(intelligence_data):
    """
    Persists calculated recommendation to the MySQL `reorder_recommendations` table.
    Deduplication: Replaces previous recommendation for product on calculation_date.
    """
    product_id = intelligence_data["product_id"]
    calc_date = intelligence_data["calculation_date"]

    del_sql = "DELETE FROM reorder_recommendations WHERE product_id = %s AND calculation_date = %s"
    execute_db(del_sql, (product_id, calc_date))

    ins_sql = """
        INSERT INTO reorder_recommendations (
            product_id, calculation_date, predicted_demand, current_stock,
            safety_stock, lead_time_demand, recommended_quantity, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_db(ins_sql, (
        product_id,
        calc_date,
        intelligence_data["forecasted_demand"],
        intelligence_data["current_stock"],
        intelligence_data["safety_stock"],
        intelligence_data["lead_time_demand"],
        intelligence_data["recommended_quantity"],
        "Pending"
    ))



def get_all_inventory_intelligence(horizon_days=7):
    """
    Computes and persists inventory intelligence & recommendations for all active catalog products.
    """
    products_sql = "SELECT product_id FROM products ORDER BY product_id ASC"
    products = query_db(products_sql)

    results = []
    for p in products:
        try:
            intel = calculate_product_inventory_intelligence(p["product_id"], horizon_days)
            persist_reorder_recommendation(intel)
            results.append(intel)
        except Exception as e:
            continue

    return results
