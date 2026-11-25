"""Reporting SQL and chart scales for the overview and analytics pages."""

from decimal import Decimal, ROUND_CEILING

from operations_sql import FLIGHT_SUMMARY

SUMMARY = f"""
    SELECT COUNT(*) AS flights,
           COALESCE(SUM(booked_seats), 0) AS confirmed,
           COALESCE(SUM(revenue), 0) AS revenue,
           COALESCE(ROUND(AVG(100.0 * booked_seats / capacity), 2), 0) AS occupancy,
           (SELECT COUNT(*) FROM BOOKING WHERE Status = 'Cancelled') AS cancelled,
           (SELECT COUNT(*) FROM PASSENGER) AS passengers,
           (SELECT COUNT(*) FROM AIRLINE) AS airlines,
           (SELECT COUNT(*) FROM AIRCRAFT) AS aircraft
    FROM ({FLIGHT_SUMMARY}) AS flights
"""

AIRLINE_REVENUE = """
    SELECT al.Airline_Name AS airline, COUNT(DISTINCT f.Flight_id) AS flights,
           COUNT(b.Bk_id) AS confirmed, COALESCE(SUM(b.AmountPaid), 0) AS revenue
    FROM AIRLINE al
    LEFT JOIN AIRCRAFT a ON a.Airline_ID = al.Airline_ID
    LEFT JOIN FLIGHT_SCHEDULE f ON f.Ac_id = a.Ac_id
    LEFT JOIN BOOKING b ON b.Flight_id = f.Flight_id AND b.Status = 'Confirmed'
    GROUP BY al.Airline_ID, al.Airline_Name
    ORDER BY revenue DESC, al.Airline_Name
"""

# Accessible text values accompany both CSS charts. The database supplies
# every metric. The transformations below only assign colors and chart scales.
COLORS = ("#5988ff", "#a68af9", "#44c3c4", "#edb269", "#e788a8", "#8bc98e")


def revenue_chart(rows):
    total = sum(row["revenue"] for row in rows)
    start = Decimal(0)
    segments = []
    entries = []
    for index, row in enumerate(rows):
        share = row["revenue"] * 100 / total if total else Decimal(0)
        color = COLORS[index % len(COLORS)]
        segments.append(f"{color} {start:.4f}% {start + share:.4f}%")
        entries.append(dict(row, color=color, share=share))
        start += share
    fill = "conic-gradient(" + ", ".join(segments) + ")" if total else "#303848"
    return {"rows": entries, "total": total, "fill": fill}


def occupancy_chart(rows):
    maximum = max((row["occupancy"] for row in rows), default=0)
    # Four equally spaced ticks, with a minimum quarter-percent interval.
    ceiling = max(Decimal(1), Decimal(maximum).to_integral_value(rounding=ROUND_CEILING))
    step = ceiling / 4
    return {"rows": rows, "ceiling": ceiling, "ticks": [step * n for n in range(4, -1, -1)]}
