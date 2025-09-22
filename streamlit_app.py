
import streamlit as st
import pandas as pd
import numpy as np
import uuid
import time
import socket
from pathlib import Path
from optimizer import solve_plan

# ---------- App Config & Theme ----------
st.set_page_config(
    page_title="Kararı Tasarlayanlar – Canlı Demo",
    layout="wide",
    page_icon="🧭"
)
PRIMARY = "#FF9500"   # Bright Orange
ACCENT  = "#00DCB0"   # Like Cyan
SECOND  = "#008069"   # Noble Green
YELLOW  = "#FFC12B"

# ---------- Data Paths ----------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SUPPLIERS_CSV = DATA_DIR / "suppliers.csv"
PRODUCERS_CSV = DATA_DIR / "producers.csv"
CUSTOMERS_CSV = DATA_DIR / "customers.csv"

# ---------- Utils ----------
def append_row(csv_path: Path, row: dict):
    df = pd.DataFrame([row])
    if csv_path.exists():
        df.to_csv(csv_path, mode="a", index=False, header=False)
    else:
        df.to_csv(csv_path, index=False)

def load_df(csv_path: Path, cols: list):
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df[cols]

def local_ip():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception:
        return "127.0.0.1"

def app_url_hint():
    ip = local_ip()
    return f"http://{ip}:8501"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"<h2 style='color:{PRIMARY};margin-bottom:0'>🎭 Rolünüz</h2>", unsafe_allow_html=True)
    role = st.selectbox("Rol seçin", ["Tedarikçi", "Üretimci", "Müşteri", "Finans", "Kontrol Paneli"])
    st.caption("🔁 Çok katılımcı: Herkes aynı ağa bağlı olmalı. Veriler CSV dosyalarına yazılır ve pano canlı okur.")
    st.markdown("---")
    st.markdown("**Bağlantı İpucu**")
    st.code(app_url_hint(), language="bash")
    st.caption("Bu adresi QR'a dönüştürüp paylaşabilirsiniz. (Örn. quickchart, goqr)")

st.markdown(f"<h1 style='margin:0 0 8px 0'>Karar Alanlar Değil, <span style='color:{PRIMARY}'>Kararı Tasarlayanlar</span> Çağı</h1>", unsafe_allow_html=True)
st.caption("Katılımcılar QR ile rol alır, veri girer; sistem tahmin + optimizasyon ile **kararı tasarlar**.")

tabs = st.tabs(["Katılımcı Girişi", "Kontrol Paneli", "Simülasyon"])

# ---------- Tab 1: Katılımcı Girişi ----------
with tabs[0]:
    if role == "Tedarikçi":
        st.subheader("🧩 Tedarikçi Girişi")
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            supplier_id = st.text_input("Tedarikçi Adı/Kodu", placeholder="Örn: SUP-A", value=f"SUP-{str(uuid.uuid4())[:4]}")
            price = st.number_input("Birim Fiyat (₺)", min_value=0.0, value=100.0, step=1.0, help="Daha düşük daha iyi")
        with col2:
            lead = st.number_input("Teslim Süresi (gün)", min_value=0.0, value=5.0, step=0.5, help="Daha düşük daha iyi")
            cap = st.number_input("Kapasite (adet)", min_value=0.0, value=100.0, step=10.0)
        with col3:
            co2 = st.number_input("Karbon Skoru", min_value=0.0, value=1.0, step=0.1, help="Daha düşük daha iyi")
            st.write(" ")
            if st.button("Gönder", use_container_width=True):
                if supplier_id.strip() == "":
                    st.error("Tedarikçi kodu boş bırakılamaz.")
                else:
                    append_row(SUPPLIERS_CSV, {
                        "supplier_id": supplier_id, "price": price, "lead_days": lead, "co2": co2, "capacity": cap, "ts": time.time()
                    })
                    st.success("Kaydedildi!")
    elif role == "Üretimci":
        st.subheader("🏭 Üretimci Girişi")
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            plant = st.text_input("Hat/Fabrika Kodu", placeholder="Örn: PLANT-1", value=f"PLANT-{str(uuid.uuid4())[:4]}")
            prod_cost = st.number_input("Üretim Maliyeti (₺/adet)", min_value=0.0, value=50.0, step=1.0)
        with col2:
            prod_cap = st.number_input("Günlük Kapasite (adet)", min_value=0.0, value=200.0, step=10.0)
        with col3:
            defect = st.number_input("Hata Oranı (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
            st.write(" ")
            if st.button("Gönder", use_container_width=True):
                if plant.strip() == "":
                    st.error("Hat/Fabrika kodu boş bırakılamaz.")
                else:
                    append_row(PRODUCERS_CSV, {
                        "plant": plant, "prod_cost": prod_cost, "prod_cap": prod_cap, "defect_pct": defect, "ts": time.time()
                    })
                    st.success("Kaydedildi!")
    elif role == "Müşteri":
        st.subheader("🧑‍💼 Müşteri Talebi")
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            customer = st.text_input("Müşteri Kodu", placeholder="Örn: CUST-1", value=f"CUST-{str(uuid.uuid4())[:4]}")
            demand = st.number_input("Talep (adet)", min_value=1, value=150, step=1)
        with col2:
            max_price = st.number_input("Maks Fiyat (₺)", min_value=0.0, value=180.0, step=1.0)
        with col3:
            max_lead = st.number_input("Maks Teslim (gün)", min_value=0.0, value=7.0, step=0.5)
            st.write(" ")
            if st.button("Gönder", use_container_width=True):
                if customer.strip() == "":
                    st.error("Müşteri kodu boş bırakılamaz.")
                else:
                    append_row(CUSTOMERS_CSV, {
                        "customer": customer, "demand": demand, "max_price": max_price, "max_lead": max_lead, "ts": time.time()
                    })
                    st.success("Kaydedildi!")
    elif role == "Finans":
        st.subheader("💰 Finans Parametreleri")
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            capex_limit = st.number_input("Nakit Limit (₺)", min_value=0.0, value=50000.0, step=1000.0)
        with col2:
            w_price = st.slider("Fiyat Ağırlığı", 0.0, 1.0, 0.5)
            w_lead = st.slider("Teslim Ağırlığı", 0.0, 1.0, 0.3)
        with col3:
            w_co2  = st.slider("CO₂ Ağırlığı", 0.0, 1.0, 0.2)
            st.write(" ")
            if st.button("Güncelle / Öner", use_container_width=True):
                st.session_state["fin_params"] = {"capex_limit": capex_limit, "w_price": w_price, "w_lead": w_lead, "w_co2": w_co2}
                st.success("Finans parametreleri güncellendi.")
        st.info("Not: Finans parametreleri oturum bazlıdır. Kontrol Paneli'nden de ayarlanabilir.")
    else:
        st.info("Kontrol Paneli'ne üstteki sekmeden erişebilirsiniz.")

# ---------- Tab 2: Kontrol Paneli ----------
with tabs[1]:
    st.subheader("🛠 Kontrol Paneli (Admin)")

    sup_cols = ["supplier_id", "price", "lead_days", "co2", "capacity", "ts"]
    pro_cols = ["plant", "prod_cost", "prod_cap", "defect_pct", "ts"]
    cus_cols = ["customer", "demand", "max_price", "max_lead", "ts"]
    df_sup = load_df(SUPPLIERS_CSV, sup_cols)
    df_pro = load_df(PRODUCERS_CSV, pro_cols)
    df_cus = load_df(CUSTOMERS_CSV, cus_cols)

    topA, topB, topC, topD = st.columns([1,1,1,1])
    with topA:
        if st.button("🧹 Temizle (Tedarikçi)"):
            if SUPPLIERS_CSV.exists(): SUPPLIERS_CSV.unlink()
    with topB:
        if st.button("🧹 Temizle (Üretim)"):
            if PRODUCERS_CSV.exists(): PRODUCERS_CSV.unlink()
    with topC:
        if st.button("🧹 Temizle (Müşteri)"):
            if CUSTOMERS_CSV.exists(): CUSTOMERS_CSV.unlink()
    with topD:
        if st.button("🧹 Hepsini Temizle"):
            for p in [SUPPLIERS_CSV, PRODUCERS_CSV, CUSTOMERS_CSV]:
                if p.exists(): p.unlink()

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("### 📦 Tedarikçiler")
        st.dataframe(df_sup, use_container_width=True)
        st.markdown("### 🧑‍💼 Müşteriler")
        st.dataframe(df_cus, use_container_width=True)
    with col2:
        st.markdown("### 🏭 Üretim")
        st.dataframe(df_pro, use_container_width=True)

        # Quick analytics cards
        st.markdown("---")
        demand_total = float(df_cus["demand"].sum()) if len(df_cus) else 0.0
        prod_total = float(df_pro["prod_cap"].sum()) if len(df_pro) else 0.0
        sup_total = float(df_sup["capacity"].sum()) if len(df_sup) else 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Talep", int(demand_total))
        m2.metric("Üretim Kapasitesi", int(prod_total))
        m3.metric("Tedarik Kapasitesi", int(sup_total))

    # Predictive scoring heuristic
    st.markdown("### 🔮 Dönüşüm Olasılığı (Hızlı Skor)")
    if len(df_cus) and len(df_sup):
        fin = st.session_state.get("fin_params", {"capex_limit": 50000.0, "w_price": 0.5, "w_lead": 0.3, "w_co2": 0.2})
        df_sup = df_sup.copy()
        # weighted score (lower better)
        df_sup["weighted"] = fin["w_price"]*(df_sup["price"]/max(1.0, df_sup["price"].max())) + \
                             fin["w_lead"]*(df_sup["lead_days"]/max(1.0, df_sup["lead_days"].max())) + \
                             fin["w_co2"]*(df_sup["co2"]/max(1.0, df_sup["co2"].max()))
        best_sup = df_sup.sort_values("weighted").head(1)
        if len(best_sup):
            bp = float(best_sup["price"].iloc[0])
            bl = float(best_sup["lead_days"].iloc[0])
            df_score = df_cus.copy()
            df_score["price_gap"] = (df_score["max_price"] - bp) / df_score["max_price"].replace(0, np.nan)
            df_score["lead_gap"]  = (df_score["max_lead"] - bl) / df_score["max_lead"].replace(0, np.nan)
            df_score["price_gap"] = df_score["price_gap"].clip(-1,1).fillna(0)
            df_score["lead_gap"]  = df_score["lead_gap"].clip(-1,1).fillna(0)
            df_score["conv_prob"] = (0.5 + 0.5*(0.6*df_score["price_gap"] + 0.4*df_score["lead_gap"])).clip(0,1)
            st.dataframe(df_score[["customer","demand","max_price","max_lead","conv_prob"]], use_container_width=True)
        else:
            st.info("Skor için en az bir tedarikçi gerekiyor.")
    else:
        st.info("Skor için hem müşteri hem tedarik verisi girilmeli.")

    # Optimization button
    st.markdown("### 🧮 Optimizasyon – Plan Öner (PuLP)")
    if st.button("Planı Hesapla"):
        if len(df_sup) and len(df_pro) and demand_total > 0:
            fin = st.session_state.get("fin_params", {"capex_limit": 50000.0, "w_price": 0.5, "w_lead": 0.3, "w_co2": 0.2})
            plan, kpis = solve_plan(df_sup, df_pro, demand_total, fin)
            st.success("Plan hazırlandı.")
            st.write("**Tahsis Planı (tedarikçi → miktar)**")
            st.dataframe(pd.DataFrame(plan.items(), columns=["Tedarikçi","Miktar"]), use_container_width=True)
            st.write("**KPI'lar**")
            st.json(kpis)
        else:
            st.warning("Optimizasyon için en az bir tedarikçi, üretimci ve müşteri talebi gerekir.")

# ---------- Tab 3: Simülasyon ----------
with tabs[2]:
    st.subheader("🧪 What-if Simülasyonu (sahne için hızlı etkiler)")
    st.caption("Aşağıdaki kaydırgaçlar sadece **görsel** amaçlıdır; canlı veriyi manipüle etmez.")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sim_price = st.slider("Tedarikçi Fiyat Daralması (%)", -20, 20, 0)
    with col2:
        sim_lead = st.slider("Teslim Süresi Değişimi (gün)", -3, 3, 0)
    with col3:
        sim_dem  = st.slider("Talep Şoku (%)", -30, 30, 0)
    with col4:
        sim_co2  = st.slider("CO₂ Artışı (%)", -30, 30, 0)

    # Pull current data
    sup_cols = ["supplier_id", "price", "lead_days", "co2", "capacity", "ts"]
    cus_cols = ["customer", "demand", "max_price", "max_lead", "ts"]
    df_sup = load_df(SUPPLIERS_CSV, sup_cols).copy()
    df_cus = load_df(CUSTOMERS_CSV, cus_cols).copy()

    if len(df_sup):
        df_sup["price_sim"] = df_sup["price"] * (1 + sim_price/100.0)
        df_sup["lead_sim"]  = df_sup["lead_days"] + sim_lead
        df_sup["co2_sim"]   = df_sup["co2"] * (1 + sim_co2/100.0)
        st.markdown("**Tedarikçi Simülasyonu**")
        st.dataframe(df_sup[["supplier_id","price","price_sim","lead_days","lead_sim","co2","co2_sim","capacity"]], use_container_width=True)
    else:
        st.info("Simülasyon için en az bir tedarikçi girin.")

    if len(df_cus):
        df_cus["demand_sim"] = (df_cus["demand"] * (1 + sim_dem/100.0)).round().astype(int)
        st.markdown("**Talep Simülasyonu**")
        st.dataframe(df_cus[["customer","demand","demand_sim","max_price","max_lead"]], use_container_width=True)
    else:
        st.info("Simülasyon için en az bir müşteri girin.")

    st.caption("Gerçek karar için Kontrol Paneli'nden **Planı Hesapla** düğmesini kullanın.")
