-- =====================================================================
-- Hospitality data model (SQLite).  All primary keys are UUID strings.
-- Extends the reference model (Hotel, Guest, Employee) with:
--   room_types : room inventory per hotel (needed for "available rooms")
--   bookings   : associative entity = the Hotel-Guest relationship
--                (carries check-in/out, rate, revenue, channel)
--   surveys    : guest feedback (needed for Guest Satisfaction Score)
-- Hotel-Employee relationship = employees.hotel_id (FK)
-- =====================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE hotels (
    hotel_id      TEXT PRIMARY KEY,
    hotel_name    TEXT NOT NULL,
    location      TEXT NOT NULL,
    state         TEXT NOT NULL,
    hotel_type    TEXT NOT NULL,          -- Beach Resort / Business Hotel / ...
    star_rating   INTEGER NOT NULL,
    total_rooms   INTEGER NOT NULL
);

CREATE TABLE room_types (
    room_type_id  TEXT PRIMARY KEY,
    hotel_id      TEXT NOT NULL REFERENCES hotels(hotel_id),
    room_type     TEXT NOT NULL,          -- Standard / Deluxe / Suite
    room_count    INTEGER NOT NULL,
    base_rate     REAL NOT NULL           -- rack rate in INR (2021 prices)
);

CREATE TABLE guests (
    guest_id      TEXT PRIMARY KEY,
    guest_name    TEXT NOT NULL,
    email         TEXT,
    phone         TEXT,
    city          TEXT,
    country       TEXT,
    loyalty_tier  TEXT                    -- Blue / Silver / Gold / Platinum
);

CREATE TABLE employees (
    employee_id        TEXT PRIMARY KEY,
    employee_name      TEXT NOT NULL,
    position           TEXT NOT NULL,
    department         TEXT NOT NULL,
    hotel_id           TEXT NOT NULL REFERENCES hotels(hotel_id),
    hire_date          TEXT NOT NULL,     -- YYYY-MM-DD
    termination_date   TEXT,              -- NULL = still employed
    termination_reason TEXT,
    is_seasonal        INTEGER NOT NULL,  -- 1 = seasonal hire
    monthly_salary     REAL
);

CREATE TABLE bookings (
    booking_id        TEXT PRIMARY KEY,
    guest_id          TEXT NOT NULL REFERENCES guests(guest_id),
    hotel_id          TEXT NOT NULL REFERENCES hotels(hotel_id),
    room_type_id      TEXT NOT NULL REFERENCES room_types(room_type_id),
    booking_date      TEXT NOT NULL,
    check_in_date     TEXT NOT NULL,
    check_out_date    TEXT NOT NULL,
    nights            INTEGER NOT NULL,
    rooms_booked      INTEGER NOT NULL,
    nightly_rate      REAL NOT NULL,      -- INR per room per night
    total_room_revenue REAL NOT NULL,     -- 0 for Cancelled / No-Show
    booking_status    TEXT NOT NULL,      -- Completed / Cancelled / No-Show
    booking_channel   TEXT NOT NULL,      -- Direct / OTA / Corporate / Travel Agent
    segment           TEXT NOT NULL       -- Leisure / Business / Family / Group
);

CREATE TABLE surveys (
    survey_id          TEXT PRIMARY KEY,
    booking_id         TEXT NOT NULL REFERENCES bookings(booking_id),
    guest_id           TEXT NOT NULL REFERENCES guests(guest_id),
    hotel_id           TEXT NOT NULL REFERENCES hotels(hotel_id),
    survey_date        TEXT NOT NULL,
    overall_score      INTEGER NOT NULL,  -- 1..10
    service_score      INTEGER NOT NULL,
    cleanliness_score  INTEGER NOT NULL
);

CREATE INDEX ix_bookings_hotel_in  ON bookings(hotel_id, check_in_date);
CREATE INDEX ix_bookings_status    ON bookings(booking_status);
CREATE INDEX ix_bookings_guest     ON bookings(guest_id);
CREATE INDEX ix_surveys_hotel      ON surveys(hotel_id);
CREATE INDEX ix_employees_hotel    ON employees(hotel_id, hire_date, termination_date);
