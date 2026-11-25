from fastapi import APIRouter, Request

from database import transaction
from operations_sql import FLIGHT_SUMMARY
from reporting import AIRLINE_REVENUE, SUMMARY, occupancy_chart, revenue_chart
from reservation_store import BOOKING_SELECT
from ui import render

router = APIRouter()


@router.get("/")
def overview(request: Request):
    # One InnoDB snapshot keeps all dashboard panels consistent during bookings.
    with transaction() as cursor:
        cursor.execute(SUMMARY)
        summary = cursor.fetchone()
        cursor.execute(AIRLINE_REVENUE)
        revenue = revenue_chart(cursor.fetchall())
        cursor.execute(FLIGHT_SUMMARY + " ORDER BY occupancy DESC, flight_id LIMIT 7")
        occupancy = occupancy_chart(cursor.fetchall())
        cursor.execute(BOOKING_SELECT + " ORDER BY b.BookingDate DESC, b.Bk_id DESC LIMIT 5")
        recent = cursor.fetchall()
        cursor.execute(FLIGHT_SUMMARY + " ORDER BY departure_time DESC, flight_id LIMIT 4")
        schedule = cursor.fetchall()
    return render(request, "dashboard.html", title="Overview", summary=summary,
                  revenue=revenue, occupancy=occupancy, recent=recent, schedule=schedule)
