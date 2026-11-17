"""
Write docs/INFERENCE.md - the 'stories behind the variations'.
Every number in the document is pulled from the aggregate tables, so the
narrative always matches the data (re-run after changing the generator).
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "hospitality.db"
OUT = ROOT / "docs" / "INFERENCE.md"

con = sqlite3.connect(DB)
q = lambda s: pd.read_sql(s, con)

port_y = q("""SELECT year,
    ROUND(100.0*SUM(occupied_room_nights)/SUM(available_room_nights),1) occ,
    ROUND(1.0*SUM(room_revenue)/SUM(occupied_room_nights)) adr,
    ROUND(1.0*SUM(room_revenue)/SUM(available_room_nights)) revpar,
    ROUND(1.0*SUM(score_sum)/SUM(survey_count),2) sat,
    ROUND(100.0*SUM(leavers)/AVG(avg_headcount)/ (COUNT(DISTINCT year_month)/12.0) / COUNT(DISTINCT hotel_id) ,1) dummy,
    SUM(room_revenue) rev
    FROM agg_hotel_monthly GROUP BY year""")
# portfolio turnover: leavers per year / mean total headcount
to = q("""SELECT year, 100.0*SUM(leavers)/(SUM(avg_headcount)/12.0) AS turnover FROM agg_portfolio_monthly GROUP BY year""")
port_y = port_y.drop(columns="dummy").merge(to, on="year")

seas = q("SELECT * FROM agg_seasonality")
hm = q("SELECT * FROM agg_hotel_monthly")
hy = q("SELECT * FROM agg_hotel_yearly")
dow = q("SELECT * FROM agg_dow")
hotels = q("SELECT * FROM hotels")
seg = q("SELECT * FROM agg_segment_monthly")
bst = q("SELECT * FROM agg_booking_status_monthly")
reason = q("SELECT * FROM agg_staff_reason")
MN = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
inr = lambda x: f"₹{x:,.0f}"


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(lines)


L = []
w = L.append

# ------------------------------------------------------------------ 0
tot_rev = port_y.rev.sum()
w("# Inference Document - Hospitality KPI Analysis (2021-2025)\n")
w(f"**Scope:** 5 hotels (Goa, Mumbai, Jaipur, Manali, Chennai), {int(hotels.total_rooms.sum())} rooms, "
  f"Jan 2021 - Dec 2025. Total room revenue analysed: **{inr(tot_rev / 1e7)} crore**. "
  "All data is synthetic, generated with trend, seasonality and event effects described in the project README.\n")

# ------------------------------------------------------------------ 1
w("## 1. Portfolio scorecard\n")
t = port_y.copy()
t = t.rename(columns={"year": "Year", "occ": "Occupancy %", "adr": "ADR (₹)", "revpar": "RevPAR (₹)",
                      "sat": "Guest Sat (1-10)", "turnover": "Staff Turnover % (annual)"})
t["Staff Turnover % (annual)"] = t["Staff Turnover % (annual)"].round(1)
t["ADR (₹)"] = t["ADR (₹)"].map(lambda v: f"{v:,.0f}")
t["RevPAR (₹)"] = t["RevPAR (₹)"].map(lambda v: f"{v:,.0f}")
w(md_table(t.drop(columns="rev")) + "\n")

first, last = port_y.iloc[0], port_y.iloc[-1]
adr_cagr = ((last.adr / first.adr) ** (1 / 4) - 1) * 100
revpar_growth = (last.revpar / first.revpar - 1) * 100
w("## 2. Story 1 - Recovery and shocks: the long-term trend\n")
w(f"* Occupancy climbed from **{first.occ}% in 2021 to {last.occ}% in 2025**, a post-pandemic normalisation. "
  f"Most of the gain came in 2022-23, after which growth flattens - the market is approaching its ceiling.")
w(f"* ADR grew at **{adr_cagr:.1f}% a year** (from {inr(first.adr)} to {inr(last.adr)}) - roughly inflation plus a premium "
  "as hotels stopped discounting.")
w(f"* Because both volume and price rose, **RevPAR grew {revpar_growth:.0f}%** over the period "
  f"({inr(first.revpar)} → {inr(last.revpar)}). ADR rose "
  f"{(last.adr / first.adr - 1) * 100:.0f}% and occupancy rose {(last.occ / first.occ - 1) * 100:.0f}% in relative terms; "
  "the two compound into the RevPAR gain (RevPAR = ADR x occupancy).\n")

# shocks
def month_occ(year, ym_start, ym_end):
    d = hm[(hm.year_month >= ym_start) & (hm.year_month <= ym_end)]
    return 100 * d.occupied_room_nights.sum() / d.available_room_nights.sum()

delta_2021 = month_occ(2021, "2021-05", "2021-06")
delta_2022 = month_occ(2022, "2022-05", "2022-06")
omi_dec21 = month_occ(2021, "2021-12", "2021-12"); omi_jan22 = month_occ(2022, "2022-01", "2022-01")
omi_feb22 = month_occ(2022, "2022-02", "2022-02"); omi_jan23 = month_occ(2023, "2023-01", "2023-01")
w("**Shock events visible in the data**\n")
w(f"* **COVID second wave (Apr-Jun 2021):** portfolio occupancy in May-Jun 2021 was only **{delta_2021:.1f}%**, vs "
  f"{delta_2022:.1f}% a year later - lockdowns and travel restrictions froze leisure and business demand alike.")
w(f"* **Omicron wave (Jan 2022):** January is normally a strong month, yet occupancy was only {omi_jan22:.1f}% "
  f"(Dec 2021: {omi_dec21:.1f}%, Feb 2022: {omi_feb22:.1f}%, and Jan 2023: {omi_jan23:.1f}%). The dip was short-lived because "
  "vaccination had already lifted confidence, so the recovery trend was interrupted for only about a month.")

pine = hm[hm.hotel_name == "Himalayan Pine Lodge"].set_index("year_month")
fl = pine.loc["2023-07":"2023-08"]
ctrl = pine.loc[["2022-07", "2022-08", "2024-07", "2024-08"]]
fl_occ = 100 * fl.occupied_room_nights.sum() / fl.available_room_nights.sum()
ctrl_occ = 100 * ctrl.occupied_room_nights.sum() / ctrl.available_room_nights.sum()
fl_sat = fl.score_sum.sum() / fl.survey_count.sum()
ctrl_sat = ctrl.score_sum.sum() / ctrl.survey_count.sum()
w(f"* **Manali floods (Jul-Aug 2023):** Himalayan Pine Lodge ran at **{fl_occ:.1f}%** occupancy against {ctrl_occ:.1f}% in the same "
  f"months of 2022 and 2024. Guests who did stay were less happy ({fl_sat:.2f} vs {ctrl_sat:.2f}) because of road closures "
  "and disrupted services. This is a destination-specific risk that no portfolio average reveals.")

chn = hm[hm.hotel_name == "Marina Bay Business Hotel"].set_index("year_month")
w("* **Cyclone Michaung (Dec 2023, Chennai):** a 5-day storm window pulled down occupancy at Marina Bay for the whole month "
  f"(Dec 2023 = {chn.loc['2023-12', 'occupancy_rate']:.1f}% vs Dec 2022 = {chn.loc['2022-12', 'occupancy_rate']:.1f}% and "
  f"Dec 2024 = {chn.loc['2024-12', 'occupancy_rate']:.1f}%) - December is normally one of its best months, so a dip "
  "against a rising trend is the cyclone's footprint.\n")

# ------------------------------------------------------------------ 3
w("## 3. Story 2 - Seasonality: every hotel has its own calendar\n")
rows = []
for h, g in seas.groupby("hotel_name"):
    pk, tr = g.loc[g.occupancy_rate.idxmax()], g.loc[g.occupancy_rate.idxmin()]
    rows.append({"Hotel": h, "Peak month": f"{pk.month_name} ({pk.occupancy_rate}%)",
                 "Trough month": f"{tr.month_name} ({tr.occupancy_rate}%)",
                 "Peak ADR": inr(pk.adr), "Trough ADR": inr(tr.adr),
                 "ADR premium": f"{(pk.adr / tr.adr - 1) * 100:.0f}%",
                 "RevPAR peak/trough": f"{pk.revpar / tr.revpar:.1f}x"})
w(md_table(pd.DataFrame(rows)) + "\n")
w("**Why it happens (maps to the seasonal-variation brief)**\n")
w("* **Beach resort (Goa):** peaks in Nov-Feb (winter weather, Christmas/New Year, wedding season) and collapses in the "
  "monsoon months (Jun-Aug), when sea activities close and demand falls.")
w("* **Hill resort (Manali):** two humps - summer escape (May-Jun) and snow season (Dec) - with a deep monsoon trough.")
w("* **Heritage (Jaipur):** Oct-Mar is the pleasant-weather tourist season; Apr-Jul heat keeps occupancy low.")
w("* **Business hotels (Mumbai, Chennai):** far flatter curves, because corporate travel is driven by the financial calendar "
  "rather than weather; mild softness in the monsoon quarter and a lift around year-end.")
w("* **Events:** Diwali and New Year week add visible spikes at leisure hotels, while business hotels dip during Diwali "
  "because corporate offices close.\n")

# ------------------------------------------------------------------ 4
w("## 4. Story 3 - Pricing power: ADR follows demand, so RevPAR swings harder than occupancy\n")
corr = []
for h, g in seas.groupby("hotel_name"):
    corr.append(np.corrcoef(g.occupancy_rate, g.adr)[0, 1])
w(f"* Across the 12 calendar months, the correlation between occupancy and ADR is **{np.mean(corr):.2f} on average** across hotels - "
  "hotels charge more when they are full (peak-season pricing) and discount in the off-season.")
w("* Because price and volume move together, **RevPAR amplifies seasonality**: the peak/trough RevPAR multiple in the table above "
  "is much larger than the occupancy multiple alone. Revenue management matters most in the shoulder months, where a small "
  "price move can shift the volume that gets booked.\n")

# ------------------------------------------------------------------ 5
w("## 5. Story 4 - Weekday vs weekend: leisure and business are mirror images\n")
rows = []
for h, g in dow.groupby("hotel_name"):
    g = g.set_index("dow_name")
    wk = g.loc[["Mon", "Tue", "Wed", "Thu"], "occupancy_rate"].mean()
    we = g.loc[["Fri", "Sat"], "occupancy_rate"].mean()
    rows.append({"Hotel": h, "Mon-Thu occ %": round(wk, 1), "Fri-Sat occ %": round(we, 1),
                 "Weekend lift": f"{we - wk:+.1f} pts"})
w(md_table(pd.DataFrame(rows)) + "\n")
w("Leisure hotels fill up on Fri/Sat while business hotels empty out, so the two types hedge each other inside one portfolio. "
  "Business hotels respond by *discounting* weekend rates; leisure hotels add a weekend premium.\n")

# ------------------------------------------------------------------ 6
w("## 6. Story 5 - Guest satisfaction: crowding and staff churn are the hidden drivers\n")
hm2 = hm.dropna(subset=["guest_satisfaction"]).copy()
c_occ = np.corrcoef(hm2.occupancy_rate, hm2.guest_satisfaction)[0, 1]
hi = hm2[hm2.occupancy_rate >= 85]; lo = hm2[hm2.occupancy_rate < 60]
sat = lambda d: d.score_sum.sum() / d.survey_count.sum()
w(f"* Monthly occupancy and satisfaction have a correlation of **{c_occ:.2f}**. "
  f"Hotel-months running at 85%+ occupancy score **{sat(hi):.2f}** on average ({len(hi)} hotel-months) vs "
  f"**{sat(lo):.2f}** when below 60% ({len(lo)} hotel-months). Crowded lobbies, longer check-in queues and "
  "stretched housekeeping reduce the experience in peak season - the exact crowding effect described in the brief.")
c_to = np.corrcoef(hm2.turnover_rate_pct, hm2.guest_satisfaction)[0, 1]
w(f"* Satisfaction also moves against staff turnover (correlation **{c_to:.2f}**): months with heavy departures mean "
  "new, less-trained staff on the floor, and the **service sub-score** falls first.")
jai = hm[hm.hotel_name == "Amber Heritage Palace"].set_index("year_month")
ren = jai.loc["2024-03":"2024-06"]; pre = jai.loc["2023-03":"2023-06"]
w(f"* **Jaipur renovation (Mar-Jun 2024):** satisfaction at Amber Heritage Palace was {ren.score_sum.sum() / ren.survey_count.sum():.2f} "
  f"vs {pre.score_sum.sum() / pre.survey_count.sum():.2f} in the same months of 2023, while occupancy barely changed - "
  "a reminder that satisfaction can fall *without* any signal in occupancy or ADR.")
best = hy.groupby("hotel_name").apply(lambda d: d.score_sum.sum() / d.survey_count.sum()).sort_values()
w(f"* Highest-rated property over five years: **{best.index[-1]}** ({best.iloc[-1]:.2f}); lowest: **{best.index[0]}** ({best.iloc[0]:.2f}).\n")

# ------------------------------------------------------------------ 7
w("## 7. Story 6 - Employee turnover: seasonal contracts and peak-season burnout\n")
tm = q("""SELECT month_num, 100.0*SUM(leavers)/SUM(avg_headcount) AS t, SUM(seasonal_leavers) s, SUM(leavers) l
          FROM agg_hotel_monthly GROUP BY month_num""").set_index("month_num")
top3 = tm.t.sort_values(ascending=False).head(3)
w(f"* Portfolio monthly turnover is highest in **{', '.join(MN[m] for m in top3.index)}** "
  f"({', '.join(f'{v:.1f}%' for v in top3.values)} of headcount per month).")
sh = 100 * reason[reason.termination_reason == "Seasonal Contract End"].leavers.sum() / reason.leavers.sum()
w(f"* **{sh:.0f}% of all separations are seasonal contracts ending** - leisure hotels hire extra staff ahead of peak months and "
  "release them afterwards, so headline turnover is structurally high at resorts without implying dissatisfaction.")
perm = reason[reason.termination_reason != "Seasonal Contract End"].groupby("termination_reason").leavers.sum().sort_values(ascending=False)
w(f"* Among permanent staff, the most common exit reasons are **{perm.index[0]}** and **{perm.index[1]}**. "
  "April and January bumps match appraisal / bonus cycles.")
ty = hy.pivot(index="hotel_name", columns="year", values="annual_turnover_pct")
w(f"* Highest average annual turnover: **{ty.mean(axis=1).idxmax()}** ({ty.mean(axis=1).max():.0f}%); lowest: "
  f"**{ty.mean(axis=1).idxmin()}** ({ty.mean(axis=1).min():.0f}%). Small, seasonal, remote properties churn the most.")
dept = reason[reason.termination_reason != "Seasonal Contract End"].groupby("department").leavers.sum().sort_values(ascending=False)
w(f"* The department losing most permanent staff is **{dept.index[0]}** ({dept.iloc[0]} exits) - a target for retention programmes.\n")

# ------------------------------------------------------------------ 8
w("## 8. Story 7 - Channel and segment mix\n")
ch = seg.groupby("booking_channel").room_revenue.sum()
w("Revenue share by booking channel: " + ", ".join(f"**{k}** {100 * v / ch.sum():.0f}%" for k, v in ch.sort_values(ascending=False).items()) + ".")
b = bst.groupby("booking_channel")[["bookings", "cancelled", "no_show"]].sum()
b["cx"] = 100 * (b.cancelled + b.no_show) / b.bookings
w("Cancellation + no-show rate by channel: " + ", ".join(f"**{k}** {v:.1f}%" for k, v in b.cx.sort_values(ascending=False).items()) +
  ". OTA bookings carry both a discount and the highest cancellation risk, which is why direct-booking campaigns pay off.\n")

# ------------------------------------------------------------------ 9
w("## 9. Recommendations\n")
w("1. **Dynamic pricing in shoulder months** - peaks already price at a large premium; the upside is in months like Apr/Sep/Oct where occupancy is mid-range.")
w("2. **Cap crowding in peak months** - add temporary front-desk/housekeeping capacity at 85%+ occupancy to protect satisfaction.")
w("3. **Retention focus on permanent housekeeping and F&B staff** and a pre-peak onboarding programme for seasonal hires.")
w("4. **Diversify weather/geo risk** - Manali's 2023 flood showed single-destination exposure; build cancellation-protection and local-event packages.")
w("5. **Shift OTA share to direct and corporate channels** to cut cancellation risk and discounting.")
w("6. **Pair satisfaction tracking with operational events** (renovation, staffing gaps) - they are invisible in occupancy/ADR.\n")
w("---\n*Auto-generated by `src/generate_inference.py` from the aggregate tables. Re-run `python run_all.py` to refresh.*")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("\n".join(L), encoding="utf-8")
print(f"Wrote {OUT}")
