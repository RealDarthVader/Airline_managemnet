"""Validate HTML form values before opening a write transaction."""

import re
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


async def read_form(request: Request) -> dict[str, str]:
    async with request.form() as data:
        return {key: value for key, value in data.items() if isinstance(value, str)}


FormValues = Annotated[dict[str, str], Depends(read_form)]
DatabaseID = Annotated[int, Field(ge=-2147483648, le=2147483647)]


class FormModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)


class BookingInput(FormModel):
    passenger_id: DatabaseID
    flight_id: str = Field(min_length=1, max_length=15)
    ticket_id: DatabaseID
    seat_no: str = Field(min_length=1, max_length=8)
    status: Literal["Confirmed", "Pending"]
    payment_method: str = Field(min_length=1, max_length=30)
    amount_paid: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @field_validator("seat_no", mode="before")
    @classmethod
    def normalize_seat(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class ContactInput(FormModel):
    email: str = Field(min_length=1, max_length=150)
    phones: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter an email address such as name@example.com")
        return value

    @field_validator("phones", mode="before")
    @classmethod
    def split_phone_numbers(cls, value):
        if isinstance(value, str):
            value = re.split(r"[,\r\n]+", value)
        return list(dict.fromkeys(phone.strip() for phone in value if phone.strip()))

    @field_validator("phones")
    @classmethod
    def validate_phone_numbers(cls, values):
        if any(len(phone) > 20 for phone in values):
            raise ValueError("Each phone number can contain up to 20 characters")
        return values


class PassengerInput(ContactInput):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)


def validation_messages(error: ValidationError) -> list[str]:
    labels = {
        "passenger_id": "Passenger", "ticket_id": "Ticket", "flight_id": "Flight",
        "seat_no": "Seat number", "amount_paid": "Amount paid", "phones": "Phone numbers",
    }
    messages = []
    for item in error.errors():
        key = str(item["loc"][0])
        label = labels.get(key, key.replace("_", " ").capitalize())
        if item["type"] == "missing" or item.get("input") == "":
            messages.append(f"{label} is required.")
        else:
            reason = item["msg"].removeprefix("Value error, ")
            messages.append(f"{label} — {reason.rstrip('.')}.")
    return messages
