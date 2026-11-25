from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from database import fetch_all, fetch_one
from operations_sql import CITIES, CREW, CREW_ORDER, FLIGHT_BOOKINGS, FLIGHT_SUMMARY, filtered_query
from schemas import DatabaseID
from ui import render

router = APIRouter()


@router.get("/flights", name="flights")
def flights(request: Request, source: DatabaseID | Literal[""] = "", destination: DatabaseID | Literal[""] = ""):
    query, params = filtered_query(
        FLIGHT_SUMMARY,
        [("dep.City_ID", source), ("arr.City_ID", destination)],
        " ORDER BY f.DepartureTime, f.Flight_id",
    )
    return render(
        request, "flights.html", title="Flights",
        flights=fetch_all(query, params), cities=fetch_all(CITIES),
        source=source, destination=destination,
    )


@router.get("/flights/{flight_id}", name="flight_details")
def flight_details(request: Request, flight_id: str):
    flight = fetch_one(FLIGHT_SUMMARY + " WHERE f.Flight_id = %s", (flight_id,))
    if not flight:
        raise HTTPException(status_code=404, detail="This flight is not on the schedule.")
    crew = fetch_all(CREW + " WHERE sa.Flight_id = %s" + CREW_ORDER, (flight_id,))
    bookings = fetch_all(FLIGHT_BOOKINGS, (flight_id,))
    return render(
        request, "flight_details.html", title=flight["flight_id"],
        flight=flight, crew=crew, bookings=bookings,
    )
