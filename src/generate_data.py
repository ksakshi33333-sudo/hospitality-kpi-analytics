"""
Generate 5 years (2021-2025) of realistic hospitality sample data with pandas.

* Primary keys are UUID v4 (seeded, so the run is reproducible)
* Names are realistic (Faker en_IN / en_US name pools)
* Seasonality, growth trend, day-of-week effects and one-off events are
  deliberately baked in so the dashboard tells real stories.

Output: CSV files in data/raw/
"""
import random
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
START = pd.Timestamp("2021-01-01")
END = pd.Timestamp("2025-12-31")
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"

rnd = random.Random(SEED)
rng = np.random.default_rng(SEED)


def uid() -> str:
    """Reproducible UUID v4."""
    return str(uuid.UUID(int=rnd.getrandbits(128), version=4))


# ---------------------------------------------------------------------
# 1. CONFIGURATION  - this is where trends & seasonal variation live
# ---------------------------------------------------------------------
# season = occupancy multiplier for Jan..Dec ; dow = multiplier Mon..Sun
LEISURE_DOW = [0.88, 0.88, 0.90, 0.95, 1.15, 1.25, 1.05]
BUSINESS_DOW = [1.12, 1.15, 1.15, 1.05, 0.90, 0.75, 0.80]
LEISURE_RATE_DOW = [0.95, 0.95, 0.95, 1.00, 1.12, 1.15, 1.00]
BUSINESS_RATE_DOW = [1.05, 1.05, 1.05, 1.00, 0.92, 0.88, 0.90]

HOTELS = [
    dict(name="Azure Sands Beach Resort", location="Calangute, Goa", state="Goa",
         htype="Beach Resort", stars=5, rooms={"Standard": 70, "Deluxe": 90, "Suite": 40},
         rates={"Standard": 6500, "Deluxe": 8800, "Suite": 15500},
         base_occ=0.58, los=3.4, sat_base=8.1,
         season=[1.20, 1.10, 0.95, 0.75, 0.65, 0.50, 0.45, 0.50, 0.60, 0.90, 1.25, 1.45],
         dow=LEISURE_DOW, rdow=LEISURE_RATE_DOW,
         mix={"Leisure": .50, "Family": .35, "Group": .10, "Business": .05}),
    dict(name="Marine Drive Business Hotel", location="Mumbai", state="Maharashtra",
         htype="Business Hotel", stars=5, rooms={"Standard": 90, "Deluxe": 70, "Suite": 20},
         rates={"Standard": 8200, "Deluxe": 10500, "Suite": 19000},
         base_occ=0.70, los=2.0, sat_base=7.8,
         season=[1.05, 1.05, 1.00, 0.95, 0.90, 0.85, 0.85, 0.90, 1.00, 1.10, 1.10, 1.10],
         dow=BUSINESS_DOW, rdow=BUSINESS_RATE_DOW,
         mix={"Business": .62, "Leisure": .20, "Group": .13, "Family": .05}),
    dict(name="Amber Heritage Palace", location="Jaipur", state="Rajasthan",
         htype="Heritage Hotel", stars=5, rooms={"Standard": 40, "Deluxe": 50, "Suite": 30},
         rates={"Standard": 7000, "Deluxe": 9500, "Suite": 18000},
         base_occ=0.60, los=2.6, sat_base=8.4,
         season=[1.15, 1.10, 1.00, 0.75, 0.60, 0.55, 0.65, 0.70, 0.85, 1.20, 1.30, 1.30],
         dow=LEISURE_DOW, rdow=LEISURE_RATE_DOW,
         mix={"Leisure": .50, "Family": .25, "Group": .15, "Business": .10}),
    dict(name="Himalayan Pine Lodge", location="Manali", state="Himachal Pradesh",
         htype="Hill Resort", stars=4, rooms={"Standard": 40, "Deluxe": 30, "Suite": 10},
         rates={"Standard": 4800, "Deluxe": 6500, "Suite": 11000},
         base_occ=0.55, los=3.0, sat_base=8.0,
         season=[0.95, 0.85, 0.90, 1.15, 1.50, 1.50, 0.70, 0.65, 0.75, 1.00, 0.80, 1.30],
         dow=LEISURE_DOW, rdow=LEISURE_RATE_DOW,
         mix={"Leisure": .45, "Family": .38, "Group": .12, "Business": .05}),
    dict(name="Marina Bay Business Hotel", location="Chennai", state="Tamil Nadu",
         htype="Business Hotel", stars=4, rooms={"Standard": 80, "Deluxe": 55, "Suite": 15},
         rates={"Standard": 5600, "Deluxe": 7400, "Suite": 13500},
         base_occ=0.68, los=2.1, sat_base=7.9,
         season=[1.05, 1.00, 0.95, 0.90, 0.85, 0.90, 0.95, 1.00, 1.05, 1.05, 1.00, 1.10],
         dow=BUSINESS_DOW, rdow=BUSINESS_RATE_DOW,
         mix={"Business": .60, "Leisure": .22, "Group": .12, "Family": .06}),
]

DIWALI = {2021: "2021-11-04", 2022: "2022-10-24", 2023: "2023-11-12",
          2024: "2024-11-01", 2025: "2025-10-20"}

# (scope, start, end, occupancy_mult, rate_mult, label)
# scope: None = all hotels | hotel name | "leisure" | "business"
EVENTS = [
    (None, "2021-04-20", "2021-06-30", 0.45, 0.92, "COVID second (Delta) wave"),
    (None, "2022-01-05", "2022-02-10", 0.70, 0.95, "Omicron wave"),
    ("Himalayan Pine Lodge", "2023-07-08", "2023-08-25", 0.35, 0.90, "Himachal floods / landslides"),
    ("Marina Bay Business Hotel", "2023-12-03", "2023-12-07", 0.55, 1.00, "Cyclone Michaung"),
]
for y, d in DIWALI.items():
    dd = pd.Timestamp(d)
    EVENTS.append(("leisure", dd - pd.Timedelta(days=2), dd + pd.Timedelta(days=4), 1.12, 1.10, "Diwali"))
    EVENTS.append(("business", dd - pd.Timedelta(days=1), dd + pd.Timedelta(days=3), 0.85, 1.00, "Diwali (corporate holiday)"))
for y in range(2021, 2026):
    EVENTS.append(("leisure", f"{y}-12-27", f"{y + 1}-01-01", 1.12, 1.18, "New Year week"))

# score events: (hotel, start, end, delta)
SAT_EVENTS = [
    ("Himalayan Pine Lodge", "2023-07-08", "2023-08-25", -0.7),
    ("Amber Heritage Palace", "2024-03-01", "2024-06-30", -0.6),   # renovation noise
]

POSITIONS = [  # (position, department, share_of_staff, monthly_salary_INR)
    ("Front Desk Agent", "Front Office", 0.10, 28000),
    ("Concierge", "Front Office", 0.04, 32000),
    ("Bell Captain", "Front Office", 0.07, 20000),
    ("Housekeeping Attendant", "Housekeeping", 0.26, 19000),
    ("Chef de Partie", "Food & Beverage", 0.10, 42000),
    ("F&B Server", "Food & Beverage", 0.15, 22000),
    ("Maintenance Technician", "Engineering", 0.08, 30000),
    ("Security Guard", "Security", 0.07, 21000),
    ("Sales Executive", "Sales & Marketing", 0.04, 45000),
    ("Department Manager", "Management", 0.06, 75000),
    ("Spa Therapist", "Wellness", 0.03, 24000),
]
POS_P = np.array([p[2] for p in POSITIONS])
LEAVE_REASONS = ["Resignation", "Better Opportunity", "Relocation", "Retirement", "Dismissal"]
LEAVE_P = [0.35, 0.35, 0.10, 0.03, 0.17]

CHANNELS = ["Direct", "OTA", "Corporate", "Travel Agent"]
CHANNEL_BY_SEGMENT = {
    "Leisure": [.30, .50, .00, .20], "Family": [.35, .45, .00, .20],
    "Business": [.25, .20, .50, .05], "Group": [.20, .10, .30, .40],
}
CHANNEL_DISCOUNT = {"Direct": 1.00, "OTA": 0.93, "Corporate": 0.88, "Travel Agent": 0.95}
LEAD_DAYS = {"Business": 5, "Leisure": 14, "Family": 18, "Group": 25}

ROOMS_PER_BOOKING = 1.18      # mean of [1,2,3] with p=[.85,.12,.03]
COMPLETE_SHARE = 0.89         # share of bookings that end up 'Completed'
PRICE_INFLATION = 0.055       # yearly ADR drift


def trend_factor(t_years):
    """Post-COVID recovery curve: 0.82 -> ~1.09 over 5 years."""
    t = np.maximum(t_years, 0)
    return 0.82 + 0.28 * (1 - np.exp(-t / 1.8))


# ---------------------------------------------------------------------
# 2. NAME POOLS
# ---------------------------------------------------------------------
Faker.seed(SEED)
_fk_in, _fk_us = Faker("en_IN"), Faker("en_US")
FIRST_IN = sorted({_fk_in.first_name() for _ in range(4000)})
LAST_IN = sorted({_fk_in.last_name() for _ in range(4000)})
FIRST_INTL = sorted({_fk_us.first_name() for _ in range(2000)})
LAST_INTL = sorted({_fk_us.last_name() for _ in range(2000)})

IN_CITIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata",
             "Ahmedabad", "Jaipur", "Kochi", "Chandigarh", "Lucknow", "Indore", "Coimbatore", "Surat"]
IN_CITY_P = np.array([.14, .14, .13, .09, .08, .08, .06, .05, .03, .03, .03, .03, .03, .03, .03])
IN_CITY_P = IN_CITY_P / IN_CITY_P.sum()
INTL = [("United States", "New York"), ("United Kingdom", "London"), ("United Arab Emirates", "Dubai"),
        ("Germany", "Berlin"), ("Australia", "Sydney"), ("Singapore", "Singapore")]


# ---------------------------------------------------------------------
# 3. HOTELS & ROOM TYPES
# ---------------------------------------------------------------------
def make_hotels():
    hotels, rts = [], []
    for h in HOTELS:
        h["hotel_id"] = uid()
        hotels.append(dict(hotel_id=h["hotel_id"], hotel_name=h["name"], location=h["location"],
                           state=h["state"], hotel_type=h["htype"], star_rating=h["stars"],
                           total_rooms=sum(h["rooms"].values())))
        h["rt_ids"] = {}
        for rt, cnt in h["rooms"].items():
            rid = uid()
            h["rt_ids"][rt] = rid
            rts.append(dict(room_type_id=rid, hotel_id=h["hotel_id"], room_type=rt,
                            room_count=cnt, base_rate=h["rates"][rt]))
    return pd.DataFrame(hotels), pd.DataFrame(rts)


# ---------------------------------------------------------------------
# 4. EVENTS
# ---------------------------------------------------------------------
def event_mults(dts, h):
    occ, rate = np.ones(len(dts)), np.ones(len(dts))
    for scope, s, e, om, rm, _ in EVENTS:
        ok = (scope is None or scope == h["name"]
              or (scope == "leisure" and h["htype"] != "Business Hotel")
              or (scope == "business" and h["htype"] == "Business Hotel"))
        if ok:
            mask = (dts >= pd.Timestamp(s)) & (dts <= pd.Timestamp(e))
            occ[mask] *= om
            rate[mask] *= rm
    return occ, rate


# ---------------------------------------------------------------------
# 5. BOOKINGS
# ---------------------------------------------------------------------
def make_bookings():
    frames = []
    dts = pd.date_range(START - pd.Timedelta(days=14), END)   # warm-up so Jan-1 isn't empty
    for h in HOTELS:
        month = dts.month.values
        dow = dts.dayofweek.values
        t = (dts - START).days.values / 365.25
        season = np.array(h["season"])[month - 1]
        om, rm = event_mults(dts, h)
        occ = np.minimum(h["base_occ"] * season * trend_factor(t) * np.array(h["dow"])[dow]
                         * om * rng.normal(1, 0.05, len(dts)), 0.97)
        total = sum(h["rooms"].values())
        lam = occ * total / (h["los"] * ROOMS_PER_BOOKING) / COMPLETE_SHARE
        n = rng.poisson(lam)
        di = np.repeat(np.arange(len(dts)), n)
        m = len(di)

        check_in = dts.values[di]
        nights = np.minimum(1 + rng.poisson(h["los"] - 1, m), 14)
        rooms = rng.choice([1, 2, 3], m, p=[.85, .12, .03])

        segs = list(h["mix"].keys())
        seg = rng.choice(segs, m, p=list(h["mix"].values()))
        chan = np.empty(m, dtype=object)
        for s in segs:
            idx = np.where(seg == s)[0]
            chan[idx] = rng.choice(CHANNELS, len(idx), p=CHANNEL_BY_SEGMENT[s])

        u = rng.random(m)
        p_cancel = np.where(chan == "OTA", 0.10, 0.05)
        status = np.where(u < p_cancel, "Cancelled",
                          np.where(u < p_cancel + 0.02, "No-Show", "Completed"))

        types = list(h["rooms"].keys())
        share = np.array([h["rooms"][x] for x in types], dtype=float)
        rtype = rng.choice(types, m, p=share / share.sum())

        base = pd.Series(rtype).map(h["rates"]).values.astype(float)
        price_season = 0.65 + 0.5 * season[di]
        inflation = (1 + PRICE_INFLATION) ** np.maximum(t[di], 0)
        disc = pd.Series(chan).map(CHANNEL_DISCOUNT).values.astype(float)
        rate = base * price_season * inflation * np.array(h["rdow"])[dow[di]] * rm[di] * disc
        rate = np.round(rate * rng.lognormal(0, 0.06, m) / 10) * 10

        lead = np.round(rng.gamma(2.0, pd.Series(seg).map(LEAD_DAYS).values / 2.0)).astype(int)
        df = pd.DataFrame(dict(
            hotel_id=h["hotel_id"],
            room_type_id=pd.Series(rtype).map(h["rt_ids"]).values,
            check_in_date=pd.to_datetime(check_in),
            nights=nights, rooms_booked=rooms, nightly_rate=rate,
            booking_status=status, booking_channel=chan, segment=seg, lead=lead))
        frames.append(df)

    bk = pd.concat(frames, ignore_index=True)
    bk["check_out_date"] = bk.check_in_date + pd.to_timedelta(bk.nights, unit="D")
    bk = bk[bk.check_out_date > START].reset_index(drop=True)
    bk["booking_date"] = bk.check_in_date - pd.to_timedelta(bk.lead, unit="D")
    bk["total_room_revenue"] = np.where(bk.booking_status == "Completed",
                                        bk.rooms_booked * bk.nights * bk.nightly_rate, 0.0)
    bk["booking_id"] = [uid() for _ in range(len(bk))]
    return bk.drop(columns="lead")


# ---------------------------------------------------------------------
# 6. GUESTS (repeat guests via a skewed pick from a pool)
# ---------------------------------------------------------------------
def make_guests(bk):
    n = len(bk)
    pool = int(n * 0.5)
    pick = (rng.random(n) ** 1.5 * pool).astype(int)
    used, inv = np.unique(pick, return_inverse=True)
    G = len(used)
    ids = np.array([uid() for _ in range(G)])
    bk["guest_id"] = ids[inv]

    foreign = rng.random(G) < 0.12
    first = np.where(foreign, rng.choice(FIRST_INTL, G), rng.choice(FIRST_IN, G))
    last = np.where(foreign, rng.choice(LAST_INTL, G), rng.choice(LAST_IN, G))
    city = rng.choice(IN_CITIES, G, p=IN_CITY_P).astype(object)
    country = np.array(["India"] * G, dtype=object)
    fi = rng.integers(0, len(INTL), G)
    for j in np.where(foreign)[0]:
        country[j], city[j] = INTL[fi[j]]
    domains = rng.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"], G)
    num = rng.integers(1, 999, G)
    email = [f"{a.lower()}.{b.lower()}{c}@{d}" for a, b, c, d in zip(first, last, num, domains)]
    ph = rng.integers(7_000_000_000, 9_999_999_999, G)
    phone = [f"+1-{str(p)[:3]}-{str(p)[3:6]}-{str(p)[6:10]}" if f else f"+91-{p}" for p, f in zip(ph, foreign)]
    tier = rng.choice(["Blue", "Silver", "Gold", "Platinum"], G, p=[.70, .18, .09, .03])
    return pd.DataFrame(dict(guest_id=ids, guest_name=[f"{a} {b}" for a, b in zip(first, last)],
                             email=email, phone=phone, city=city, country=country, loyalty_tier=tier))


# ---------------------------------------------------------------------
# 7. EMPLOYEES  (monthly simulation: attrition, seasonal hires, releases)
# ---------------------------------------------------------------------
def make_employees():
    rows = []

    def new_emp(h, hire, seasonal):
        k = rng.choice(len(POSITIONS), p=POS_P)
        pos, dept, _, sal = POSITIONS[k]
        return dict(employee_id=uid(),
                    employee_name=f"{rng.choice(FIRST_IN)} {rng.choice(LAST_IN)}",
                    position=pos, department=dept, hotel_id=h["hotel_id"],
                    hire_date=hire, termination_date=None, termination_reason=None,
                    is_seasonal=int(seasonal),
                    monthly_salary=round(sal * rng.uniform(0.9, 1.15), -2))

    for h in HOTELS:
        base_hc = int(sum(h["rooms"].values()) * 0.75)
        active = []
        for _ in range(base_hc):
            e = new_emp(h, START - pd.Timedelta(days=int(rng.integers(60, 2500))), False)
            active.append(e)
            rows.append(e)

        for per in pd.period_range(START, END, freq="M"):
            ms, me = per.start_time.normalize(), per.end_time.normalize()
            nd = (me - ms).days + 1
            workload = h["season"][per.month - 1] * float(trend_factor((ms - START).days / 365.25))
            # attrition: higher in busy months (stress) and after appraisal cycles (Apr, Jan)
            p_leave = 0.016 * (1 + 0.9 * max(0.0, workload - 1.0)) * {4: 1.5, 1: 1.2}.get(per.month, 1.0)
            for e in [x for x in active if not x["is_seasonal"]]:
                if rnd.random() < p_leave:
                    td = ms + pd.Timedelta(days=rnd.randint(0, nd - 1))
                    if td > e["hire_date"] + pd.Timedelta(days=30):
                        e["termination_date"] = td
                        e["termination_reason"] = rng.choice(LEAVE_REASONS, p=LEAVE_P)
                        active.remove(e)
            target = round(base_hc * (0.82 + 0.18 * workload))
            gap = target - len(active)
            if gap < 0:   # release seasonal staff first
                for e in [x for x in active if x["is_seasonal"]][:(-gap)]:
                    e["termination_date"] = me - pd.Timedelta(days=rnd.randint(0, 4))
                    e["termination_reason"] = "Seasonal Contract End"
                    active.remove(e)
            else:
                for _ in range(gap):
                    e = new_emp(h, ms + pd.Timedelta(days=rnd.randint(0, nd - 1)), workload > 1.05)
                    active.append(e)
                    rows.append(e)
    return pd.DataFrame(rows)


def monthly_turnover(emp):
    """leavers / avg headcount per hotel-month (used to couple satisfaction to staffing)."""
    hire = pd.to_datetime(emp.hire_date)
    term = pd.to_datetime(emp.termination_date)
    out = []
    for per in pd.period_range(START, END, freq="M"):
        ms, me = per.start_time.normalize(), per.end_time.normalize()
        for hid in emp.hotel_id.unique():
            m = emp.hotel_id == hid
            hs = ((hire < ms) & (term.isna() | (term >= ms)) & m).sum()
            he = ((hire <= me) & (term.isna() | (term > me)) & m).sum()
            lv = ((term >= ms) & (term <= me) & m).sum()
            out.append((hid, str(per), lv / max((hs + he) / 2, 1)))
    return pd.DataFrame(out, columns=["hotel_id", "ym", "to_rate"])


# ---------------------------------------------------------------------
# 8. SURVEYS (satisfaction depends on crowding, staff churn, events, trend)
# ---------------------------------------------------------------------
def make_surveys(bk, emp):
    comp = bk[bk.booking_status == "Completed"].copy()
    keep = rng.random(len(comp)) < np.where(comp.booking_channel == "Direct", 0.45, 0.30)
    sv = comp[keep].copy()

    # occupancy on the night before check-out (crowding proxy)
    idx0 = START - pd.Timedelta(days=14)
    span = (END - idx0).days + 20
    occ_lookup = {}
    for h in HOTELS:
        g = comp[comp.hotel_id == h["hotel_id"]]
        diff = np.zeros(span + 1)
        s = (g.check_in_date - idx0).dt.days.values
        e = (g.check_out_date - idx0).dt.days.values
        np.add.at(diff, s, g.rooms_booked.values)
        np.add.at(diff, e, -g.rooms_booked.values)
        occ_lookup[h["hotel_id"]] = np.cumsum(diff)[:-1] / sum(h["rooms"].values())
    occ = np.zeros(len(sv))
    for hid, arr in occ_lookup.items():
        m = (sv.hotel_id == hid).values
        pos = ((sv.check_out_date[m] - pd.Timedelta(days=1)) - idx0).dt.days.values
        occ[m] = arr[pos]
    sv["ym"] = sv.check_out_date.dt.strftime("%Y-%m")
    to = monthly_turnover(emp)
    sv = sv.merge(to, on=["hotel_id", "ym"], how="left")
    to_rate = sv.to_rate.fillna(0.03).values

    base = sv.hotel_id.map({h["hotel_id"]: h["sat_base"] for h in HOTELS}).values
    t = (sv.check_out_date - START).dt.days.values / 365.25
    mu = base + 0.06 * np.maximum(t, 0) - 6.0 * np.maximum(0, occ - 0.80) - 8.0 * (to_rate - 0.03)
    for name, s, e, delta in SAT_EVENTS:
        hid = next(h["hotel_id"] for h in HOTELS if h["name"] == name)
        m = (sv.hotel_id == hid) & (sv.check_out_date >= s) & (sv.check_out_date <= e)
        mu = mu + np.where(m, delta, 0)

    k = len(sv)
    clip = lambda x: np.clip(np.rint(x), 1, 10).astype(int)
    return pd.DataFrame(dict(
        survey_id=[uid() for _ in range(k)],
        booking_id=sv.booking_id.values, guest_id=sv.guest_id.values, hotel_id=sv.hotel_id.values,
        survey_date=(sv.check_out_date + pd.to_timedelta(rng.integers(1, 6, k), unit="D")).values,
        overall_score=clip(mu + rng.normal(0, 1.1, k)),
        service_score=clip(mu - 4 * (to_rate - 0.03) + rng.normal(0, 1.2, k)),
        cleanliness_score=clip(mu + 0.2 + rng.normal(0, 1.1, k))))


# ---------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hotels, room_types = make_hotels()
    print("Generating bookings ...")
    bk = make_bookings()
    print("Generating guests ...")
    guests = make_guests(bk)
    print("Generating employees ...")
    emp = make_employees()
    print("Generating surveys ...")
    surveys = make_surveys(bk, emp)

    fmt = lambda s: pd.to_datetime(s).dt.strftime("%Y-%m-%d")
    for c in ["booking_date", "check_in_date", "check_out_date"]:
        bk[c] = fmt(bk[c])
    for c in ["hire_date", "termination_date"]:
        emp[c] = fmt(emp[c])
    surveys["survey_date"] = fmt(surveys.survey_date)

    bk = bk[["booking_id", "guest_id", "hotel_id", "room_type_id", "booking_date", "check_in_date",
             "check_out_date", "nights", "rooms_booked", "nightly_rate", "total_room_revenue",
             "booking_status", "booking_channel", "segment"]]
    tables = dict(hotels=hotels, room_types=room_types, guests=guests, employees=emp,
                  bookings=bk, surveys=surveys)
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"  {name:<11} {len(df):>9,} rows")
    print(f"CSV files written to {OUT}")


if __name__ == "__main__":
    main()
