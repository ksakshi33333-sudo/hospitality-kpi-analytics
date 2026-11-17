-- =====================================================================
-- AGGREGATE LAYER  (SQLite dialect; see README for Postgres/MySQL notes)
--
-- Business logic used to join the tables
--   * Only booking_status = 'Completed' stays generate occupancy/revenue
--   * A booking is "exploded" into one row per stayed night
--     (fact_stay_night) so any date-level KPI is a simple GROUP BY
--   * Every hotel x every calendar day exists in fact_daily_hotel
--     (zero-occupancy days included) so denominators are correct
--   * Satisfaction is attributed to the month of CHECK-OUT
--   * Headcount at month start/end is derived from hire/termination dates
--
-- KPI formulas (all computed from ADDITIVE columns so they re-aggregate
-- correctly at any level - never average an average):
--   Occupancy % = occupied_room_nights / available_room_nights * 100
--   ADR         = room_revenue / occupied_room_nights
--   RevPAR      = room_revenue / available_room_nights
--   Satisfaction= sum(score) / count(surveys)
--   Turnover %  = leavers / average headcount * 100
-- =====================================================================

-- ---------- 1. Dimensions ------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
WITH RECURSIVE d(date_id) AS (
    SELECT '2021-01-01'
    UNION ALL
    SELECT date(date_id, '+1 day') FROM d WHERE date_id < '2025-12-31'
)
SELECT
    date_id,
    CAST(strftime('%Y', date_id) AS INTEGER)                    AS year,
    CAST(strftime('%m', date_id) AS INTEGER)                    AS month_num,
    CASE strftime('%m', date_id)
        WHEN '01' THEN 'Jan' WHEN '02' THEN 'Feb' WHEN '03' THEN 'Mar'
        WHEN '04' THEN 'Apr' WHEN '05' THEN 'May' WHEN '06' THEN 'Jun'
        WHEN '07' THEN 'Jul' WHEN '08' THEN 'Aug' WHEN '09' THEN 'Sep'
        WHEN '10' THEN 'Oct' WHEN '11' THEN 'Nov' ELSE 'Dec' END AS month_name,
    strftime('%Y-%m', date_id)                                  AS year_month,
    (CAST(strftime('%m', date_id) AS INTEGER) + 2) / 3          AS quarter,
    (CAST(strftime('%w', date_id) AS INTEGER) + 6) % 7 + 1      AS dow_num,   -- Mon=1
    CASE (CAST(strftime('%w', date_id) AS INTEGER) + 6) % 7 + 1
        WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu'
        WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat' ELSE 'Sun' END      AS dow_name
FROM d;
CREATE UNIQUE INDEX ix_dim_date ON dim_date(date_id);

DROP TABLE IF EXISTS dim_month;
CREATE TABLE dim_month AS
SELECT year_month, MIN(date_id) AS month_start, MAX(date_id) AS month_end,
       MIN(year) AS year, MIN(month_num) AS month_num, MIN(month_name) AS month_name
FROM dim_date GROUP BY year_month;

DROP TABLE IF EXISTS nums;
CREATE TABLE nums AS
WITH RECURSIVE n(n) AS (SELECT 0 UNION ALL SELECT n + 1 FROM n WHERE n < 30)
SELECT n FROM n;

-- ---------- 2. Facts -------------------------------------------------
DROP TABLE IF EXISTS fact_stay_night;
CREATE TABLE fact_stay_night AS
SELECT  b.booking_id, b.hotel_id, b.room_type_id,
        b.booking_channel, b.segment,
        date(b.check_in_date, '+' || n.n || ' day') AS stay_date,
        b.rooms_booked,
        b.nightly_rate,
        b.rooms_booked * b.nightly_rate             AS room_revenue
FROM bookings b
JOIN nums n ON n.n < b.nights
WHERE b.booking_status = 'Completed';
CREATE INDEX ix_fsn ON fact_stay_night(hotel_id, stay_date);

DROP TABLE IF EXISTS fact_daily_hotel;
CREATE TABLE fact_daily_hotel AS
WITH s AS (
    SELECT hotel_id, stay_date,
           SUM(rooms_booked) AS rooms_occupied,
           SUM(room_revenue) AS room_revenue
    FROM fact_stay_night GROUP BY hotel_id, stay_date
)
SELECT  d.date_id, h.hotel_id,
        h.total_rooms                      AS available_rooms,
        COALESCE(s.rooms_occupied, 0)      AS rooms_occupied,
        COALESCE(s.room_revenue, 0)        AS room_revenue
FROM dim_date d
CROSS JOIN hotels h
LEFT JOIN s ON s.hotel_id = h.hotel_id AND s.stay_date = d.date_id;
CREATE INDEX ix_fdh ON fact_daily_hotel(hotel_id, date_id);

-- ---------- 3. Monthly building blocks ------------------------------
DROP TABLE IF EXISTS agg_survey_monthly;
CREATE TABLE agg_survey_monthly AS
SELECT  s.hotel_id,
        substr(b.check_out_date, 1, 7) AS year_month,
        COUNT(*)                       AS survey_count,
        SUM(s.overall_score)           AS score_sum,
        SUM(s.service_score)           AS service_sum,
        SUM(s.cleanliness_score)       AS cleanliness_sum
FROM surveys s
JOIN bookings b ON b.booking_id = s.booking_id
GROUP BY s.hotel_id, substr(b.check_out_date, 1, 7);

DROP TABLE IF EXISTS agg_staff_monthly;
CREATE TABLE agg_staff_monthly AS
SELECT  m.year_month, h.hotel_id,
        (SELECT COUNT(*) FROM employees e
          WHERE e.hotel_id = h.hotel_id AND e.hire_date < m.month_start
            AND (e.termination_date IS NULL OR e.termination_date >= m.month_start)) AS headcount_start,
        (SELECT COUNT(*) FROM employees e
          WHERE e.hotel_id = h.hotel_id AND e.hire_date <= m.month_end
            AND (e.termination_date IS NULL OR e.termination_date > m.month_end))    AS headcount_end,
        (SELECT COUNT(*) FROM employees e
          WHERE e.hotel_id = h.hotel_id
            AND e.termination_date BETWEEN m.month_start AND m.month_end)            AS leavers,
        (SELECT COUNT(*) FROM employees e
          WHERE e.hotel_id = h.hotel_id
            AND e.termination_date BETWEEN m.month_start AND m.month_end
            AND e.termination_reason = 'Seasonal Contract End')                      AS seasonal_leavers
FROM dim_month m CROSS JOIN hotels h;

-- ---------- 4. KPI tables (what the dashboard reads) ---------------
DROP TABLE IF EXISTS agg_hotel_monthly;
CREATE TABLE agg_hotel_monthly AS
WITH rooms AS (
    SELECT d.year_month, f.hotel_id,
           SUM(f.available_rooms) AS available_room_nights,
           SUM(f.rooms_occupied)  AS occupied_room_nights,
           SUM(f.room_revenue)    AS room_revenue
    FROM fact_daily_hotel f JOIN dim_date d ON d.date_id = f.date_id
    GROUP BY d.year_month, f.hotel_id
)
SELECT  r.year_month, m.year, m.month_num, m.month_name,
        r.hotel_id, h.hotel_name, h.location,
        r.available_room_nights, r.occupied_room_nights, r.room_revenue,
        COALESCE(sv.survey_count, 0)  AS survey_count,
        COALESCE(sv.score_sum, 0)     AS score_sum,
        st.headcount_start, st.headcount_end,
        (st.headcount_start + st.headcount_end) / 2.0 AS avg_headcount,
        st.leavers, st.seasonal_leavers,
        -- KPIs
        ROUND(100.0 * r.occupied_room_nights / r.available_room_nights, 2)       AS occupancy_rate,
        ROUND(1.0 * r.room_revenue / NULLIF(r.occupied_room_nights, 0), 2)       AS adr,
        ROUND(1.0 * r.room_revenue / r.available_room_nights, 2)                 AS revpar,
        ROUND(1.0 * sv.score_sum / NULLIF(sv.survey_count, 0), 3)                AS guest_satisfaction,
        ROUND(100.0 * st.leavers / NULLIF((st.headcount_start + st.headcount_end) / 2.0, 0), 2) AS turnover_rate_pct
FROM rooms r
JOIN dim_month m            ON m.year_month = r.year_month
JOIN hotels h               ON h.hotel_id   = r.hotel_id
LEFT JOIN agg_survey_monthly sv ON sv.hotel_id = r.hotel_id AND sv.year_month = r.year_month
LEFT JOIN agg_staff_monthly  st ON st.hotel_id = r.hotel_id AND st.year_month = r.year_month;

DROP TABLE IF EXISTS agg_portfolio_monthly;
CREATE TABLE agg_portfolio_monthly AS
SELECT  year_month, year, month_num, month_name,
        SUM(available_room_nights) AS available_room_nights,
        SUM(occupied_room_nights)  AS occupied_room_nights,
        SUM(room_revenue)          AS room_revenue,
        SUM(survey_count)          AS survey_count,
        SUM(score_sum)             AS score_sum,
        SUM(avg_headcount)         AS avg_headcount,
        SUM(leavers)               AS leavers,
        ROUND(100.0 * SUM(occupied_room_nights) / SUM(available_room_nights), 2) AS occupancy_rate,
        ROUND(1.0 * SUM(room_revenue) / SUM(occupied_room_nights), 2)            AS adr,
        ROUND(1.0 * SUM(room_revenue) / SUM(available_room_nights), 2)           AS revpar,
        ROUND(1.0 * SUM(score_sum) / SUM(survey_count), 3)                       AS guest_satisfaction,
        ROUND(100.0 * SUM(leavers) / SUM(avg_headcount), 2)                      AS turnover_rate_pct
FROM agg_hotel_monthly
GROUP BY year_month, year, month_num, month_name;

DROP TABLE IF EXISTS agg_hotel_yearly;
CREATE TABLE agg_hotel_yearly AS
SELECT  year, hotel_id, hotel_name,
        SUM(available_room_nights) AS available_room_nights,
        SUM(occupied_room_nights)  AS occupied_room_nights,
        SUM(room_revenue)          AS room_revenue,
        SUM(survey_count)          AS survey_count,
        SUM(score_sum)             AS score_sum,
        SUM(leavers)               AS leavers,
        AVG(avg_headcount)         AS avg_headcount,
        ROUND(100.0 * SUM(occupied_room_nights) / SUM(available_room_nights), 2) AS occupancy_rate,
        ROUND(1.0 * SUM(room_revenue) / SUM(occupied_room_nights), 2)            AS adr,
        ROUND(1.0 * SUM(room_revenue) / SUM(available_room_nights), 2)           AS revpar,
        ROUND(1.0 * SUM(score_sum) / SUM(survey_count), 3)                       AS guest_satisfaction,
        ROUND(100.0 * SUM(leavers) / AVG(avg_headcount), 2)                      AS annual_turnover_pct
FROM agg_hotel_monthly
GROUP BY year, hotel_id, hotel_name;

-- Seasonality: calendar month averaged over all 5 years
DROP TABLE IF EXISTS agg_seasonality;
CREATE TABLE agg_seasonality AS
SELECT  month_num, month_name, hotel_id, hotel_name,
        ROUND(100.0 * SUM(occupied_room_nights) / SUM(available_room_nights), 2) AS occupancy_rate,
        ROUND(1.0 * SUM(room_revenue) / SUM(occupied_room_nights), 2)            AS adr,
        ROUND(1.0 * SUM(room_revenue) / SUM(available_room_nights), 2)           AS revpar,
        ROUND(1.0 * SUM(score_sum) / NULLIF(SUM(survey_count), 0), 3)            AS guest_satisfaction,
        ROUND(100.0 * SUM(leavers) / SUM(avg_headcount), 2)                      AS turnover_rate_pct
FROM agg_hotel_monthly
GROUP BY month_num, month_name, hotel_id, hotel_name;

-- Day-of-week pattern
DROP TABLE IF EXISTS agg_dow;
CREATE TABLE agg_dow AS
SELECT  d.dow_num, d.dow_name, f.hotel_id, h.hotel_name,
        ROUND(100.0 * SUM(f.rooms_occupied) / SUM(f.available_rooms), 2)          AS occupancy_rate,
        ROUND(1.0 * SUM(f.room_revenue) / NULLIF(SUM(f.rooms_occupied), 0), 2)    AS adr,
        ROUND(1.0 * SUM(f.room_revenue) / SUM(f.available_rooms), 2)              AS revpar
FROM fact_daily_hotel f
JOIN dim_date d ON d.date_id = f.date_id
JOIN hotels h   ON h.hotel_id = f.hotel_id
GROUP BY d.dow_num, d.dow_name, f.hotel_id, h.hotel_name;

-- Segment / channel mix by month
DROP TABLE IF EXISTS agg_segment_monthly;
CREATE TABLE agg_segment_monthly AS
SELECT  substr(stay_date, 1, 7) AS year_month,
        CAST(substr(stay_date, 1, 4) AS INTEGER) AS year,
        f.hotel_id, h.hotel_name, f.segment, f.booking_channel,
        SUM(f.rooms_booked) AS room_nights,
        SUM(f.room_revenue) AS room_revenue
FROM fact_stay_night f JOIN hotels h ON h.hotel_id = f.hotel_id
WHERE stay_date <= '2025-12-31'
GROUP BY 1, 2, 3, 4, 5, 6;

-- Booking status / cancellations by month
DROP TABLE IF EXISTS agg_booking_status_monthly;
CREATE TABLE agg_booking_status_monthly AS
SELECT  substr(check_in_date, 1, 7) AS year_month, hotel_id, booking_channel,
        COUNT(*) AS bookings,
        SUM(booking_status = 'Completed') AS completed,
        SUM(booking_status = 'Cancelled') AS cancelled,
        SUM(booking_status = 'No-Show')   AS no_show
FROM bookings
WHERE check_in_date >= '2021-01-01'
GROUP BY 1, 2, 3;

-- Why do people leave?
DROP TABLE IF EXISTS agg_staff_reason;
CREATE TABLE agg_staff_reason AS
SELECT  CAST(substr(e.termination_date, 1, 4) AS INTEGER) AS year,
        e.hotel_id, h.hotel_name, e.department, e.position,
        e.termination_reason, e.is_seasonal,
        COUNT(*) AS leavers
FROM employees e JOIN hotels h ON h.hotel_id = e.hotel_id
WHERE e.termination_date IS NOT NULL AND e.termination_date >= '2021-01-01'
GROUP BY 1, 2, 3, 4, 5, 6, 7;
