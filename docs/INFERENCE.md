# Inference Document - Hospitality KPI Analysis (2021-2025)

**Scope:** 5 hotels (Goa, Mumbai, Jaipur, Manali, Chennai), 730 rooms, Jan 2021 - Dec 2025. Total room revenue analysed: **₹908 crore**. All data is synthetic, generated with trend, seasonality and event effects described in the project README.

## 1. Portfolio scorecard

| Year | Occupancy % | ADR (₹) | RevPAR (₹) | Guest Sat (1-10) | Staff Turnover % (annual) |
|---|---|---|---|---|---|
| 2021 | 49.2 | 10,206 | 5,024 | 8.06 | 21.2 |
| 2022 | 57.5 | 10,656 | 6,124 | 8.06 | 23.4 |
| 2023 | 62.1 | 11,333 | 7,040 | 8.09 | 22.4 |
| 2024 | 64.2 | 11,943 | 7,664 | 8.04 | 26.5 |
| 2025 | 65.5 | 12,531 | 8,204 | 8.11 | 23.1 |

## 2. Story 1 - Recovery and shocks: the long-term trend

* Occupancy climbed from **49.2% in 2021 to 65.5% in 2025**, a post-pandemic normalisation. Most of the gain came in 2022-23, after which growth flattens - the market is approaching its ceiling.
* ADR grew at **5.3% a year** (from ₹10,206 to ₹12,531) - roughly inflation plus a premium as hotels stopped discounting.
* Because both volume and price rose, **RevPAR grew 63%** over the period (₹5,024 → ₹8,204). ADR rose 23% and occupancy rose 33% in relative terms; the two compound into the RevPAR gain (RevPAR = ADR x occupancy).

**Shock events visible in the data**

* **COVID second wave (Apr-Jun 2021):** portfolio occupancy in May-Jun 2021 was only **21.0%**, vs 51.1% a year later - lockdowns and travel restrictions froze leisure and business demand alike.
* **Omicron wave (Jan 2022):** January is normally a strong month, yet occupancy was only 49.5% (Dec 2021: 75.1%, Feb 2022: 55.5%, and Jan 2023: 74.4%). The dip was short-lived because vaccination had already lifted confidence, so the recovery trend was interrupted for only about a month.
* **Manali floods (Jul-Aug 2023):** Himalayan Pine Lodge ran at **21.3%** occupancy against 39.2% in the same months of 2022 and 2024. Guests who did stay were less happy (7.21 vs 7.70) because of road closures and disrupted services. This is a destination-specific risk that no portfolio average reveals.
* **Cyclone Michaung (Dec 2023, Chennai):** a 5-day storm window pulled down occupancy at Marina Bay for the whole month (Dec 2023 = 69.7% vs Dec 2022 = 76.9% and Dec 2024 = 83.9%) - December is normally one of its best months, so a dip against a rising trend is the cyclone's footprint.

## 3. Story 2 - Seasonality: every hotel has its own calendar

| Hotel | Peak month | Trough month | Peak ADR | Trough ADR | ADR premium | RevPAR peak/trough |
|---|---|---|---|---|---|---|
| Amber Heritage Palace | Nov (84.36%) | Jun (29.62%) | ₹16,318 | ₹11,322 | 44% | 4.1x |
| Azure Sands Beach Resort | Dec (87.58%) | Jul (26.06%) | ₹15,039 | ₹9,316 | 61% | 5.4x |
| Himalayan Pine Lodge | May (75.71%) | Aug (32.95%) | ₹9,800 | ₹6,837 | 43% | 3.3x |
| Marina Bay Business Hotel | Dec (76.18%) | May (53.86%) | ₹9,222 | ₹8,220 | 12% | 1.6x |
| Marine Drive Business Hotel | Dec (80.13%) | Jun (55.49%) | ₹13,456 | ₹11,819 | 14% | 1.6x |

**Why it happens (maps to the seasonal-variation brief)**

* **Beach resort (Goa):** peaks in Nov-Feb (winter weather, Christmas/New Year, wedding season) and collapses in the monsoon months (Jun-Aug), when sea activities close and demand falls.
* **Hill resort (Manali):** two humps - summer escape (May-Jun) and snow season (Dec) - with a deep monsoon trough.
* **Heritage (Jaipur):** Oct-Mar is the pleasant-weather tourist season; Apr-Jul heat keeps occupancy low.
* **Business hotels (Mumbai, Chennai):** far flatter curves, because corporate travel is driven by the financial calendar rather than weather; mild softness in the monsoon quarter and a lift around year-end.
* **Events:** Diwali and New Year week add visible spikes at leisure hotels, while business hotels dip during Diwali because corporate offices close.

## 4. Story 3 - Pricing power: ADR follows demand, so RevPAR swings harder than occupancy

* Across the 12 calendar months, the correlation between occupancy and ADR is **0.96 on average** across hotels - hotels charge more when they are full (peak-season pricing) and discount in the off-season.
* Because price and volume move together, **RevPAR amplifies seasonality**: the peak/trough RevPAR multiple in the table above is much larger than the occupancy multiple alone. Revenue management matters most in the shoulder months, where a small price move can shift the volume that gets booked.

## 5. Story 4 - Weekday vs weekend: leisure and business are mirror images

| Hotel | Mon-Thu occ % | Fri-Sat occ % | Weekend lift |
|---|---|---|---|
| Amber Heritage Palace | 53.8 | 60.4 | +6.6 pts |
| Azure Sands Beach Resort | 48.5 | 51.4 | +2.9 pts |
| Himalayan Pine Lodge | 52.0 | 55.6 | +3.6 pts |
| Marina Bay Business Hotel | 71.2 | 62.5 | -8.7 pts |
| Marine Drive Business Hotel | 74.1 | 64.6 | -9.6 pts |

Leisure hotels fill up on Fri/Sat while business hotels empty out, so the two types hedge each other inside one portfolio. Business hotels respond by *discounting* weekend rates; leisure hotels add a weekend premium.

## 6. Story 5 - Guest satisfaction: crowding and staff churn are the hidden drivers

* Monthly occupancy and satisfaction have a correlation of **-0.32**. Hotel-months running at 85%+ occupancy score **7.85** on average (12 hotel-months) vs **8.25** when below 60% (136 hotel-months). Crowded lobbies, longer check-in queues and stretched housekeeping reduce the experience in peak season - the exact crowding effect described in the brief.
* Satisfaction also moves against staff turnover (correlation **-0.47**): months with heavy departures mean new, less-trained staff on the floor, and the **service sub-score** falls first.
* **Jaipur renovation (Mar-Jun 2024):** satisfaction at Amber Heritage Palace was 7.99 vs 8.55 in the same months of 2023, while occupancy barely changed - a reminder that satisfaction can fall *without* any signal in occupancy or ADR.
* Highest-rated property over five years: **Amber Heritage Palace** (8.43); lowest: **Marine Drive Business Hotel** (7.90).

## 7. Story 6 - Employee turnover: seasonal contracts and peak-season burnout

* Portfolio monthly turnover is highest in **Jul, Apr, Jan** (2.9%, 2.6%, 2.6% of headcount per month).
* **23% of all separations are seasonal contracts ending** - leisure hotels hire extra staff ahead of peak months and release them afterwards, so headline turnover is structurally high at resorts without implying dissatisfaction.
* Among permanent staff, the most common exit reasons are **Better Opportunity** and **Resignation**. April and January bumps match appraisal / bonus cycles.
* Highest average annual turnover: **Himalayan Pine Lodge** (34%); lowest: **Marine Drive Business Hotel** (17%). Small, seasonal, remote properties churn the most.
* The department losing most permanent staff is **Housekeeping** (141 exits) - a target for retention programmes.

## 8. Story 7 - Channel and segment mix

Revenue share by booking channel: **OTA** 33%, **Direct** 30%, **Corporate** 20%, **Travel Agent** 18%.
Cancellation + no-show rate by channel: **OTA** 12.0%, **Travel Agent** 7.1%, **Direct** 7.0%, **Corporate** 6.9%. OTA bookings carry both a discount and the highest cancellation risk, which is why direct-booking campaigns pay off.

## 9. Recommendations

1. **Dynamic pricing in shoulder months** - peaks already price at a large premium; the upside is in months like Apr/Sep/Oct where occupancy is mid-range.
2. **Cap crowding in peak months** - add temporary front-desk/housekeeping capacity at 85%+ occupancy to protect satisfaction.
3. **Retention focus on permanent housekeeping and F&B staff** and a pre-peak onboarding programme for seasonal hires.
4. **Diversify weather/geo risk** - Manali's 2023 flood showed single-destination exposure; build cancellation-protection and local-event packages.
5. **Shift OTA share to direct and corporate channels** to cut cancellation risk and discounting.
6. **Pair satisfaction tracking with operational events** (renovation, staffing gaps) - they are invisible in occupancy/ADR.

---
*Auto-generated by `src/generate_inference.py` from the aggregate tables. Re-run `python run_all.py` to refresh.*