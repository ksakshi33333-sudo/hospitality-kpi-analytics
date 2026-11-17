# Hospitality KPI Analytics: Project Documentation

## 1. Overview

This project builds a complete analytics pipeline for a hotel business. It starts with a database design, creates five years of realistic sample data, summarizes it with SQL, shows the results on a dashboard, and explains the findings in a written report.

**Business question:** How are our hotels performing, when are they busy, are guests happy, and are staff leaving?

**KPIs tracked**

| KPI | Meaning | Formula |
|---|---|---|
| Occupancy Rate | Share of rooms that were filled | Occupied room-nights / Available room-nights x 100 |
| ADR (Average Daily Rate) | Average price per occupied room per night | Room revenue / Occupied room-nights |
| RevPAR | Revenue per available room | Room revenue / Available room-nights |
| Guest Satisfaction Score | Average survey rating (1 to 10) | Sum of scores / Number of surveys |
| Employee Turnover Rate | Share of staff who left | Leavers / Average headcount x 100 |

## 2. Tools used

| Purpose | Tool |
|---|---|
| Database | SQLite (single file, no server needed) |
| Data generation | Python, Pandas, NumPy, Faker |
| Aggregation | SQL |
| Dashboard | Streamlit and Plotly |
| Documentation | Markdown |

## 3. How the project works (pipeline)

```
generate_data.py  ->  CSV files  ->  build_db.py  ->  SQLite database
                                          |
                                  schema.sql (tables)
                                  aggregates.sql (summary tables)
                                          |
                                  dashboard/app.py  ->  charts
                                          |
                                  generate_inference.py  ->  INFERENCE.md
```

`run_all.py` runs the data, database and inference steps with one command. It takes about 30 seconds.

## 4. Data model

The reference model had three entities: Hotel, Guest and Employee. I kept them and added three more, because the KPIs cannot be calculated without them.

| Table | What it stores | Why it is needed |
|---|---|---|
| hotels | 5 hotels, location, type, total rooms | Core entity |
| room_types | Standard, Deluxe, Suite counts and base rates | Gives "available rooms" |
| guests | Name, email, phone, city, country, loyalty tier | Core entity |
| bookings | Guest, hotel, dates, rooms, rate, revenue, status, channel | Hotel-Guest relationship; source of occupancy, ADR, RevPAR |
| employees | Position, department, hire date, termination date and reason | Source of turnover |
| surveys | Overall, service and cleanliness scores | Source of satisfaction |

All primary keys are UUIDs. Relationships:

- One hotel has many room types, employees and bookings.
- One guest makes many bookings.
- One booking can have one survey.

## 5. Sample data (Python and Pandas)

The generator creates data for **1 Jan 2021 to 31 Dec 2025**:

| Table | Rows (approx.) |
|---|---|
| bookings | 305,000 |
| guests | 127,000 |
| surveys | 96,000 |
| employees | 1,200 |

**Five hotels:** Goa (beach resort), Mumbai (business), Jaipur (heritage), Manali (hill resort), Chennai (business). Names come from Faker name pools and prices are in INR.

**Trends and variations built into the data**

- **Seasonality:** each hotel has its own busy and quiet months. Goa peaks in Nov to Feb, Manali in May to Jun and Dec, Jaipur in Oct to Mar. Business hotels are flatter.
- **Growth trend:** occupancy recovers after COVID and ADR grows about 5.5% a year.
- **Peak pricing:** prices rise in busy months and fall in quiet ones.
- **Day of week:** leisure hotels fill on Fri/Sat, business hotels on weekdays.
- **Events:** COVID second wave (2021), Omicron (Jan 2022), Manali floods (Jul to Aug 2023), Cyclone Michaung in Chennai (Dec 2023), Jaipur renovation (2024), Diwali and New Year spikes.
- **Satisfaction drivers:** scores fall when a hotel is very crowded or when many staff are leaving.
- **Turnover drivers:** more exits in busy months and in appraisal months (Jan and Apr). Extra seasonal staff are hired before peak months and released afterwards.
- **Booking behavior:** channels (Direct, OTA, Corporate, Travel Agent), cancellations and no-shows, lead times and repeat guests.

## 6. SQL aggregate layer

`sql/aggregates.sql` builds the summary tables. The key business logic:

1. Only bookings with status **Completed** count towards occupancy and revenue.
2. Each booking is split into **one row per night stayed** (`fact_stay_night`), so any date-based KPI is a simple GROUP BY.
3. `fact_daily_hotel` has a row for **every hotel on every day**, including empty days, so the denominators are correct.
4. Satisfaction is assigned to the month of **check-out**.
5. Headcount at the start and end of each month is calculated from hire and termination dates.
6. KPIs are always computed from **additive columns** (sums), never by averaging averages, so they stay correct at any level (hotel, month, year, portfolio).

**Main tables**

| Table | Level of detail | Used for |
|---|---|---|
| dim_date, dim_month | day / month | Calendar logic |
| fact_stay_night | booking x night | Base fact |
| fact_daily_hotel | hotel x day | Rooms available, occupied, revenue |
| agg_hotel_monthly | hotel x month | All 5 KPIs (main dashboard source) |
| agg_portfolio_monthly | month | Combined view of all hotels |
| agg_hotel_yearly | hotel x year | Yearly comparison |
| agg_seasonality | hotel x calendar month | Seasonality heatmap |
| agg_dow | hotel x weekday | Weekday pattern |
| agg_segment_monthly | hotel x month x segment x channel | Revenue mix |
| agg_booking_status_monthly | hotel x month x channel | Cancellations |
| agg_staff_reason | hotel x year x position x reason | Why staff leave |

## 7. Dashboard

Built with Streamlit and Plotly. It reads only the aggregate tables.

- **Filters:** hotels, year range, and a switch between "by hotel" and "portfolio" views.
- **KPI cards:** the five KPIs for the selected period, with change versus the previous year.
- **One panel per KPI:** occupancy, ADR, RevPAR, satisfaction and turnover.
- **Extra views:** seasonality heatmap, occupancy by weekday, satisfaction vs occupancy, revenue by segment and channel, and reasons staff leave.

## 8. Key findings

The full written analysis is in `docs/INFERENCE.md`. In summary:

- Portfolio occupancy rose from about 49% (2021) to about 65% (2025), and RevPAR grew about 63%.
- Each hotel has its own calendar. Beach and hill resorts swing sharply between seasons, while business hotels are much steadier.
- ADR follows demand, so RevPAR moves even more than occupancy.
- Leisure hotels gain on weekends and business hotels lose, so the two types balance each other.
- Crowded months have lower guest satisfaction, and months with heavy staff exits have lower service scores.
- A large share of exits at resorts are seasonal contracts ending, not unhappy staff.
- One-off events (floods, cyclone, renovation) show up clearly in single hotels but are hidden in portfolio averages.

## 9. How to run

```bash
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
streamlit run dashboard/app.py
```

## 10. Folder structure

```
run_all.py                    one-command pipeline
requirements.txt              Python dependencies
sql/schema.sql                table definitions
sql/aggregates.sql            aggregate tables and business logic
src/generate_data.py          sample data generator
src/build_db.py               builds the database
src/generate_inference.py     writes the inference document
dashboard/app.py              Streamlit dashboard
docs/INFERENCE.md             findings and stories
docs/PROJECT_DOCUMENTATION.md this document
```

## 11. Assumptions and limitations

- All data is synthetic. Patterns are designed, so they illustrate the method rather than real market behavior.
- A few peak days (about 1.4% of hotel-days) go above 100% occupancy to represent overbooking. Monthly KPIs never exceed 100%.
- The SQL uses SQLite syntax. Moving to PostgreSQL or MySQL needs small changes to date functions.
- Revenue covers room revenue only, with no food, spa or other income.

## 12. Possible improvements

- Add food and beverage and other revenue streams.
- Add forecasting of occupancy and RevPAR.
- Move to PostgreSQL and connect Power BI or Tableau.
- Add automated data quality tests.
