
from typing import Dict, Tuple
import pandas as pd
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpStatus, value
from pulp import PULP_CBC_CMD

def solve_plan(df_sup: pd.DataFrame, df_pro: pd.DataFrame, demand_total: float, fin_params: Dict) -> Tuple[Dict[str, float], Dict]:
    """
    Basit bir tedarik + üretim planı:
    - Amaç: fiyat + lead + co2 ağırlıklı toplam maliyeti minimize et
    - Kısıtlar: tedarikçi kapasitesi, üretim kapasitesi, toplam üretim >= talep
    Not: Lead/CO2 KPI etkisini maliyete gömüyoruz (normalize edilerek).
    """
    if demand_total <= 0:
        return {}, {"status": "no_demand"}

    # Normalize for cost blending
    def nz(x):
        return float(x) if float(x) != 0 else 1.0

    max_price = max(1.0, float(df_sup["price"].max() or 1.0))
    max_lead  = max(1.0, float(df_sup["lead_days"].max() or 1.0))
    max_co2   = max(1.0, float(df_sup["co2"].max() or 1.0))

    w_price = fin_params.get("w_price", 0.5)
    w_lead  = fin_params.get("w_lead", 0.3)
    w_co2   = fin_params.get("w_co2", 0.2)

    # Decision variables: amount from each supplier
    prob = LpProblem("SupplierSelection", LpMinimize)
    x = {row.supplier_id: LpVariable(f"x_{row.supplier_id}", lowBound=0) for _, row in df_sup.iterrows()}

    # Objective: blended cost
    cost_terms = []
    for _, r in df_sup.iterrows():
        cid = r.supplier_id
        price_norm = float(r.price) / max_price
        lead_norm  = float(r.lead_days) / max_lead
        co2_norm   = float(r.co2) / max_co2
        blended_unit_cost = w_price*price_norm + w_lead*lead_norm + w_co2*co2_norm
        cost_terms.append(blended_unit_cost * x[cid])
    prob += lpSum(cost_terms)

    # Constraints
    # Supplier capacity
    for _, r in df_sup.iterrows():
        prob += x[r.supplier_id] <= float(r.capacity)

    # Production capacity: total production cannot exceed sum of plant capacities
    total_prod_cap = float(df_pro["prod_cap"].sum() or 0.0)
    prob += lpSum(x.values()) <= total_prod_cap

    # Demand fulfillment (>= demand_total)
    prob += lpSum(x.values()) >= demand_total

    # Solve
    prob.solve(PULP_CBC_CMD(msg=False))

    plan = {k: float(v.value() or 0.0) for k, v in x.items()}
    used = sum(plan.values())
    status = LpStatus[prob.status]

    # KPIs (rough)
    avg_price = 0.0
    avg_lead = 0.0
    avg_co2 = 0.0
    if used > 0:
        for _, r in df_sup.iterrows():
            q = plan.get(r.supplier_id, 0.0)
            w = q / used if used > 0 else 0.0
            avg_price += w * float(r.price)
            avg_lead  += w * float(r.lead_days)
            avg_co2   += w * float(r.co2)

    kpis = {
        "status": status,
        "produced": used,
        "demand": demand_total,
        "capacity_used_pct": (used / total_prod_cap * 100.0) if total_prod_cap else 0.0,
        "avg_price": avg_price,
        "avg_lead_days": avg_lead,
        "avg_co2": avg_co2
    }
    return plan, kpis
