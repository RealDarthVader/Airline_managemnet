from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

import reservation_store as store
from schemas import ContactInput, FormValues, PassengerInput, validation_messages
from ui import render

router = APIRouter(prefix="/passengers")


def passenger_or_404(passenger_id):
    records = store.find_passengers(passenger_id=passenger_id)
    if not records:
        raise HTTPException(404, "This passenger could not be found.")
    return records[0]


@router.get("")
def passengers(request: Request, q: str = ""):
    q = q.strip()
    return render(request, "passengers.html", title="Passengers", records=store.find_passengers(q), q=q)


def passenger_form(request, values, passenger=None, errors=(), status_code=200):
    title = "Edit contact information" if passenger else "Register passenger"
    return render(request, "passenger_form.html", title=title, values=values, passenger=passenger,
                  errors=errors, status_code=status_code)


@router.get("/new")
def new_passenger(request: Request):
    return passenger_form(request, {})


@router.post("/new")
def save_passenger(request: Request, values: FormValues):
    try:
        passenger_id = store.register_passenger(PassengerInput.model_validate(values))
    except ValidationError as error:
        return passenger_form(request, values, errors=validation_messages(error), status_code=422)
    except store.FormProblem as error:
        return passenger_form(request, values, errors=[str(error)], status_code=error.status_code)
    return RedirectResponse(f"/passengers/{passenger_id}?saved=registered", status_code=303)


@router.get("/{passenger_id}")
def passenger_details(request: Request, passenger_id: int, saved: str = ""):
    passenger = passenger_or_404(passenger_id)
    return render(request, "passenger_details.html", title="Passenger profile", passenger=passenger,
                  bookings=store.find_bookings(passenger_id=passenger_id), saved=saved)


@router.get("/{passenger_id}/edit")
def edit_contact(request: Request, passenger_id: int):
    passenger = passenger_or_404(passenger_id)
    values = {"email": passenger["email"], "phones": "\n".join(passenger["phones"])}
    return passenger_form(request, values, passenger)


@router.post("/{passenger_id}/edit")
def save_contact(request: Request, passenger_id: int, values: FormValues):
    try:
        store.update_contact(passenger_id, ContactInput.model_validate(values))
    except ValidationError as error:
        return passenger_form(request, values, passenger_or_404(passenger_id), validation_messages(error), 422)
    except store.FormProblem as error:
        if error.status_code == 404:
            raise HTTPException(404, str(error)) from error
        return passenger_form(request, values, passenger_or_404(passenger_id), [str(error)], error.status_code)
    return RedirectResponse(f"/passengers/{passenger_id}?saved=updated", status_code=303)
