from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

import reservation_store as store
from database import fetch_all
from schemas import BookingInput, FormValues, validation_messages
from ui import render

router = APIRouter(prefix="/bookings")


@router.get("")
def bookings(request: Request, q: str = "", status: str = "", flight: str = "",
             created: int | None = None, cancelled: int | None = None):
    q = q.strip()
    statuses = fetch_all("SELECT DISTINCT Status AS status FROM BOOKING ORDER BY Status")
    status_options = list(dict.fromkeys(["Confirmed", "Pending", "Cancelled", *(row["status"] for row in statuses)]))
    return render(request, "bookings.html", title="Bookings",
                  records=store.find_bookings(q, status, flight), flights=fetch_all(store.FLIGHT_OPTIONS),
                  statuses=status_options, q=q, status=status, flight=flight, created=created, cancelled=cancelled)


def booking_form(request, values, errors=(), status_code=200):
    return render(request, "booking_form.html", title="New booking", status_code=status_code,
                  values=values, errors=errors, passengers=fetch_all(store.PASSENGER_OPTIONS),
                  flights=fetch_all(store.FLIGHT_OPTIONS), tickets=fetch_all(store.TICKET_OPTIONS))


@router.get("/new")
def new_booking(request: Request, flight_id: str = "", passenger_id: str = ""):
    return booking_form(request, {"flight_id": flight_id, "passenger_id": passenger_id, "status": "Confirmed"})


@router.post("/new")
def save_booking(request: Request, values: FormValues):
    try:
        booking_id = store.create_booking(BookingInput.model_validate(values))
    except ValidationError as error:
        return booking_form(request, values, validation_messages(error), 422)
    except store.FormProblem as error:
        return booking_form(request, values, [str(error)], error.status_code)
    return RedirectResponse(f"/bookings?created={booking_id}", status_code=303)


@router.get("/{booking_id}/cancel")
def confirm_cancellation(request: Request, booking_id: int):
    records = store.find_bookings(booking_id=booking_id)
    if not records:
        raise HTTPException(404, "This booking could not be found.")
    return render(request, "booking_cancel.html", title="Cancel booking", booking=records[0])


@router.post("/{booking_id}/cancel")
def apply_cancellation(booking_id: int):
    try:
        store.cancel_booking(booking_id)
    except store.FormProblem as error:
        raise HTTPException(error.status_code, str(error)) from error
    return RedirectResponse(f"/bookings?cancelled={booking_id}", status_code=303)
