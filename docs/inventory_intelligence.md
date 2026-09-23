# SmartRetail — Inventory Intelligence & Explainable Reorders

## 1. Executive Summary

SmartRetail bridges the gap between raw statistical machine learning predictions and practical retail supply chain decisions. The Inventory Intelligence Engine calculates stockout risks, overstock conditions, and exact order quantities with transparent mathematical explainability.

---

## 2. Inventory Risk Assessment Logic

```mermaid
flowchart TD
    A[Product & Current Stock Level] --> B[Fetch Stored 7-Day / 30-Day Demand Forecast]
    B --> C[Compute Lead-Time Demand: D_lead = Forecast * (LeadTime / Horizon)]
    B --> D[Compute Safety Stock: SS = Z * sigma_D * sqrt(LeadTime)]
    C & D --> E[Reorder Point ROP = D_lead + SS]
    
    A & E --> F{Current Stock <= ROP?}
    F -->|Yes| G[High / Medium Stockout Risk]
    F -->|No| H{Current Stock > Max Threshold?}
    H -->|Yes| I[Overstock Warning]
    H -->|No| J[Optimal Stock Level]
```

### Risk Classifications:
- **Critical / Stockout Risk**: When `current_stock <= Lead Time Demand + Safety Stock`
- **Low Stock Warning**: When `current_stock <= min_stock_level`
- **Overstock Risk**: When `current_stock > max_stock_level` or `current_stock > 3 * 30-day average demand`
- **Optimal / Healthy**: Stock maintains adequate buffer without tying up excess working capital.

---

## 3. Reorder Quantity Formula

The recommended replenishment quantity $Q$ is computed deterministically:

$$Q = \max\Big(0,\; \lceil \text{Required Stock} - \text{Current Stock} - \text{Stock On Order} \rceil\Big)$$

Where:
- $\text{Required Stock} = \text{Forecasted Demand (Horizon)} + \text{Safety Stock}$
- $\text{Current Stock} = \text{inventory.current\_stock}$
- $\text{Stock On Order} = \text{0 (or pending supplier deliveries)}$

---

## 4. Deterministic Explainability ("Why?" Modal)

Rather than presenting an uninterpretable AI score, SmartRetail breaks down the exact mathematical logic for store owners:

1. **Forecasted Demand**: "AI predicts you will sell **45 units** over the next 7 days."
2. **Lead Time Consideration**: "Supplier delivery takes **3 days**, requiring **19 units** during transit."
3. **Safety Buffer**: "Based on daily sales volatility ($\sigma = 2.4$), a safety stock of **15 units** protects against spikes."
4. **Current Stock Gap**: "You currently hold **10 units** in stock."
5. **Exact Recommendation**: "To cover demand and replenish safety buffer: $(45 + 15) - 10 = \mathbf{50\text{ units}}$."

This build trust and enables actionable procurement without technical confusion.
