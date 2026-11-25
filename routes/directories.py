from typing import Literal

from fastapi import APIRouter, Request

from database import fetch_all
from operations_sql import (
    ADMINISTRATORS, AIRCRAFT, AIRLINES, AIRPORTS, CITIES, COUNTRIES, CREW,
    CREW_ORDER, DESIGNATIONS, FLIGHT_IDS, TICKETS, filtered_query,
)
from schemas import DatabaseID
from ui import render

router = APIRouter()


@router.get("/aircraft", name="aircraft")
def aircraft(request: Request, airline: DatabaseID | Literal[""] = ""):
    query, params = filtered_query(AIRCRAFT, [("a.Airline_ID", airline)], " ORDER BY al.Airline_Name, a.Ac_id")
    return render(
        request, "directories.html", title="Aircraft", section="aircraft",
        subtitle="Fleet registration, operating airlines and aircraft specifications.",
        rows=fetch_all(query, params),
        filters=[("airline", "Airline", airline, fetch_all(AIRLINES))],
        headings=["Aircraft ID", "Airline", "Aircraft model", "Capacity", "Weight (kg)", "Base airport"],
    )


@router.get("/crew", name="crew")
def crew(request: Request, flight: str = "", designation: str = ""):
    query, params = filtered_query(CREW, [("sa.Flight_id", flight), ("s.Designation", designation)], CREW_ORDER)
    return render(
        request, "directories.html", title="Crew", section="crew",
        subtitle="Staff assignments, designations and flying or standby duties.",
        rows=fetch_all(query, params),
        filters=[
            ("flight", "Flight", flight, fetch_all(FLIGHT_IDS)),
            ("designation", "Designation", designation, fetch_all(DESIGNATIONS)),
        ],
        headings=["Staff ID", "Staff name", "Designation", "Flight", "Assignment date", "Duty"],
    )


@router.get("/tickets", name="tickets")
def tickets(request: Request):
    return render(
        request, "directories.html", title="Tickets", section="tickets",
        subtitle="Compare ticket classes, base fares and included services.",
        rows=fetch_all(TICKETS), filters=[],
        headings=["Ticket ID", "Class", "Base fare", "Student discount", "Extra luggage", "Flexible ticket", "Meals"],
    )


@router.get("/airports", name="airports")
def airports(request: Request, country: DatabaseID | Literal[""] = "", city: DatabaseID | Literal[""] = ""):
    query, params = filtered_query(
        AIRPORTS, [("n.Country_ID", country), ("c.City_ID", city)],
        " ORDER BY n.Country_Name, c.City_Name, p.Airport_code",
    )
    return render(
        request, "directories.html", title="Airports", section="airports",
        subtitle="Airport codes, locations and countries across the network.",
        rows=fetch_all(query, params),
        filters=[
            ("country", "Country", country, fetch_all(COUNTRIES)),
            ("city", "City", city, fetch_all(CITIES)),
        ],
        headings=["Airport code", "Airport name", "City", "Country"],
    )


@router.get("/administrators", name="administrators")
def administrators(request: Request):
    # Group flight links per person without a GROUP_CONCAT length limit.
    people = {}
    for row in fetch_all(ADMINISTRATORS):
        key = row["admin_id"]
        if key not in people:
            people[key] = {**row, "flights": []}
        if row["flight_id"] is not None:
            people[key]["flights"].append(row["flight_id"])
    return render(
        request, "directories.html", title="Administrators", section="administrators",
        subtitle="Airport administrators, contact details and managed flights.",
        rows=list(people.values()), filters=[],
        headings=["Admin ID", "Administrator", "Contact", "Assigned airport", "Managed flights"],
    )
