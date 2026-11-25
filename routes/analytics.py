from fastapi import APIRouter, Request

from database import transaction
from explorer_queries import DEMOS
from operations_sql import FLIGHT_SUMMARY
from reporting import AIRLINE_REVENUE, occupancy_chart, revenue_chart
from ui import render

router = APIRouter()


@router.get("/analytics")
def analytics(request: Request):
    with transaction() as cursor:
        cursor.execute(AIRLINE_REVENUE)
        revenue = revenue_chart(cursor.fetchall())
        cursor.execute(f"""
            SELECT f.*, DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
            FROM ({FLIGHT_SUMMARY}) AS f ORDER BY revenue_rank, flight_id
        """)
        flights = cursor.fetchall()
        cursor.execute(FLIGHT_SUMMARY + " ORDER BY occupancy DESC, flight_id LIMIT 7")
        occupancy = occupancy_chart(cursor.fetchall())
        cursor.execute(DEMOS[13].sql)
        frequent = cursor.fetchall()
        cursor.execute(DEMOS[14].sql + " ORDER BY B.AmountPaid DESC, B.Bk_id")
        payments = cursor.fetchall()
    return render(request, "analytics.html", title="Analytics", revenue=revenue, occupancy=occupancy,
                  flights=flights, frequent=frequent, payments=payments)
