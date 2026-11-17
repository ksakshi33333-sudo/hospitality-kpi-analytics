"""
Hospitality KPI dashboard (Streamlit + Plotly).
Reads ONLY the SQL aggregate tables in data/hospitality.db.

Run:  streamlit run dashboard/app.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
DB = Path(__file__).resolve().parents[1]/"
DB = Path(__file__).resolve().parents[1] / "data" / "hospitality.db"
st.set_page_config(page_title="Hospitality KPI Dashboard", page_icon="🏨", layout="wide")

if not DB.exists():
    st.error("Database not found. Run `python run_all.py` first.")
    st.stop()


@st.cache_data(show_spinner=False)
def load(table: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        return pd.read_sql(f"SELECT * FROM {table}", con)


monthly = load("agg_hotel_monthly")
monthly["month_start"] = pd.to_datetime(monthly.year_month + "-01")
seasonality = load("agg_seasonality")
dow = load("agg_dow")
segment = load("agg_segment_monthly")
status = load("agg_booking_status_monthly")
reasons = load("agg_staff_reason")
yearly = load("agg_hotel_yearly")

ADDITIVE = ["available_room_nights", "occupied_room_nights", "room_revenue",
            "survey_count", "score_sum", "avg_headcount", "leavers"]


def add_kpis(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["occupancy_rate"] = 100 * d.occupied_room_nights / d.available_room_nights
    d["adr"] = d.room_revenue / d.occupied_room_nights
    d["revpar"] = d.room_revenue / d.available_room_nights
    d["guest_satisfaction"] = d.score_sum / d.survey_count
    d["turnover_rate_pct"] = 100 * d.leavers / d.avg_headcount
    return d


def kpi_summary(d: pd.DataFrame) -> dict:
    if d.empty:
        return {k: np.nan for k in ["occ", "adr", "revpar", "sat", "turn"]}
    avail, occ, rev = d.available_room_nights.sum(), d.occupied_room_nights.sum(), d.room_revenue.sum()
    return dict(occ=100 * occ / avail, adr=rev / occ, revpar=rev / avail,
                sat=d.score_sum.sum() / d.survey_count.sum(),
                turn=12 * d.leavers.sum() / d.avg_headcount.sum() * 100)   # annualised


# ------------------------------------------------------------------ sidebar
st.sidebar.title("🏨 Filters")
all_hotels = sorted(monthly.hotel_name.unique())
sel_hotels = st.sidebar.multiselect("Hotels", all_hotels, default=all_hotels)
years = sorted(monthly.year.unique())
yr_range = st.sidebar.select_slider("Years", options=years, value=(years[0], years[-1]))
view = st.sidebar.radio("Trend lines show", ["By hotel", "Portfolio (combined)"])
st.sidebar.caption("Data: 5 synthetic hotels, 2021-2025. KPIs are recomputed from additive "
                   "columns, so every filter combination is mathematically correct.")

if not sel_hotels:
    st.warning("Select at least one hotel.")
    st.stop()

f = monthly[monthly.hotel_name.isin(sel_hotels) & monthly.year.between(*yr_range)]
if view.startswith("Portfolio"):
    trend = add_kpis(f.groupby("month_start")[ADDITIVE].sum().reset_index().assign(hotel_name="Portfolio"))
else:
    trend = f
color = "hotel_name"

# ------------------------------------------------------------------ header + KPI strip
st.title("Hospitality KPI Dashboard")
st.caption(f"{', '.join(sel_hotels) if len(sel_hotels) < len(all_hotels) else 'All hotels'} · {yr_range[0]}-{yr_range[1]}")

cur = kpi_summary(f)
prev = kpi_summary(monthly[monthly.hotel_name.isin(sel_hotels) & (monthly.year == yr_range[1] - 1)]) \
    if yr_range[1] - 1 >= years[0] else None
last_y = kpi_summary(monthly[monthly.hotel_name.isin(sel_hotels) & (monthly.year == yr_range[1])])


def delta(key, pct=False):
    if prev is None or np.isnan(prev[key]):
        return None
    d = last_y[key] - prev[key]
    return f"{(d / prev[key]) * 100:+.1f}% vs {yr_range[1] - 1}" if pct else f"{d:+.2f} vs {yr_range[1] - 1}"


c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Occupancy rate", f"{cur['occ']:.1f}%", delta("occ"))
c2.metric("ADR", f"₹{cur['adr']:,.0f}", delta("adr", True))
c3.metric("RevPAR", f"₹{cur['revpar']:,.0f}", delta("revpar", True))
c4.metric("Guest satisfaction", f"{cur['sat']:.2f} / 10", delta("sat"))
c5.metric("Staff turnover (annual)", f"{cur['turn']:.1f}%", delta("turn"))
st.caption("Big numbers = selected period. Deltas compare the last selected year with the year before it.")
st.divider()


def line_panel(col, title, ytitle, fmt=None):
    fig = px.line(trend.sort_values("month_start"), x="month_start", y=col, color=color,
                  labels={"month_start": "", col: ytitle, "hotel_name": ""}, title=title)
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    if fmt:
        fig.update_yaxes(tickformat=fmt)
    st.plotly_chart(fig, width="stretch")


# ------------------------------------------------------------------ one panel per KPI
left, right = st.columns(2)
with left:
    line_panel("occupancy_rate", "1 · Occupancy rate (%)", "Occupancy %")
with right:
    line_panel("adr", "2 · Average Daily Rate (₹)", "ADR ₹", ",.0f")

left, right = st.columns(2)
with left:
    line_panel("revpar", "3 · Revenue per Available Room (₹)", "RevPAR ₹", ",.0f")
with right:
    line_panel("guest_satisfaction", "4 · Guest satisfaction score (1-10)", "Score")

left, right = st.columns(2)
with left:
    fig = px.bar(trend.sort_values("month_start"), x="month_start", y="turnover_rate_pct", color=color,
                 barmode="group" if view.startswith("By") else "relative",
                 labels={"month_start": "", "turnover_rate_pct": "Monthly turnover %", "hotel_name": ""},
                 title="5 · Employee turnover rate (% of headcount leaving per month)")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
with right:
    ys = yearly[yearly.hotel_name.isin(sel_hotels) & yearly.year.between(*yr_range)]
    fig = px.bar(ys, x="year", y="annual_turnover_pct", color="hotel_name", barmode="group",
                 labels={"annual_turnover_pct": "Annual turnover %", "year": "", "hotel_name": ""},
                 title="5b · Annual turnover by hotel")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")

st.divider()
st.header("Seasonality & drivers")

ss = seasonality[seasonality.hotel_name.isin(sel_hotels)]
kpi_choice = st.selectbox("Seasonality heatmap KPI", ["occupancy_rate", "adr", "revpar", "guest_satisfaction", "turnover_rate_pct"])
piv = ss.pivot(index="hotel_name", columns="month_num", values=kpi_choice)
piv.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig = px.imshow(piv, aspect="auto", color_continuous_scale="YlOrRd", text_auto=".1f",
                title=f"Seasonality: {kpi_choice} by calendar month (average of all years)")
fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    d = dow[dow.hotel_name.isin(sel_hotels)].sort_values("dow_num")
    fig = px.bar(d, x="dow_name", y="occupancy_rate", color="hotel_name", barmode="group",
                 labels={"dow_name": "", "occupancy_rate": "Occupancy %", "hotel_name": ""},
                 title="Occupancy by day of week")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
with right:
    h = f.dropna(subset=["guest_satisfaction"])
    fig = px.scatter(h, x="occupancy_rate", y="guest_satisfaction", color="hotel_name",
                     hover_data=["year_month"],
                     labels={"occupancy_rate": "Monthly occupancy %", "guest_satisfaction": "Satisfaction", "hotel_name": ""},
                     title="Do full hotels disappoint guests? (each dot = hotel-month)")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    sg = segment[segment.hotel_name.isin(sel_hotels) & segment.year.between(*yr_range)]
    mix = sg.groupby(["segment", "booking_channel"], as_index=False).room_revenue.sum()
    fig = px.sunburst(mix, path=["segment", "booking_channel"], values="room_revenue",
                      title="Room revenue: segment → channel")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")
with right:
    rs = reasons[reasons.hotel_name.isin(sel_hotels) & reasons.year.between(*yr_range)]
    rr = rs.groupby("termination_reason", as_index=False).leavers.sum().sort_values("leavers")
    fig = px.bar(rr, x="leavers", y="termination_reason", orientation="h",
                 labels={"termination_reason": "", "leavers": "Employees leaving"},
                 title="Why staff leave (incl. seasonal contract ends)")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")

with st.expander("Yearly KPI table (from agg_hotel_yearly)"):
    st.dataframe(yearly[yearly.hotel_name.isin(sel_hotels) & yearly.year.between(*yr_range)]
                 [["year", "hotel_name", "occupancy_rate", "adr", "revpar", "guest_satisfaction", "annual_turnover_pct"]]
                 .round(2), hide_index=True, width="stretch")
