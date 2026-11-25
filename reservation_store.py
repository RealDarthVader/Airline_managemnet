"""Booking and passenger SQL for the supplied 14-table MySQL schema."""

from mysql.connector.errors import IntegrityError

from database import fetch_all, transaction
from schemas import BookingInput, ContactInput, PassengerInput


class FormProblem(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


FLIGHT_OPTIONS = """
    SELECT Flight_id AS flight_id, Dep_Airport_code AS origin,
           Arr_Airport_code AS destination
    FROM FLIGHT_SCHEDULE ORDER BY DepartureTime, Flight_id
"""
PASSENGER_OPTIONS = """
    SELECT Passenger_id AS passenger_id, CONCAT(FName, ' ', LName) AS name
    FROM PASSENGER ORDER BY LName, FName, Passenger_id
"""
TICKET_OPTIONS = """
    SELECT Tkt_id AS ticket_id, Class AS ticket_class, Price AS price
    FROM TICKET ORDER BY Price, Tkt_id
"""
BOOKING_SELECT = """
    SELECT b.Bk_id AS booking_id, b.Passenger_id AS passenger_id,
           CONCAT(p.FName, ' ', p.LName) AS name, b.Flight_id AS flight_id,
           t.Class AS ticket_class, b.Seat_no AS seat_no, b.BookingDate AS booking_date,
           b.PaymentMethod AS payment_method, b.AmountPaid AS amount_paid, b.Status AS status
    FROM BOOKING b
    JOIN PASSENGER p ON p.Passenger_id = b.Passenger_id
    JOIN TICKET t ON t.Tkt_id = b.Tkt_id
"""


def find_bookings(q="", status="", flight="", passenger_id=None, booking_id=None):
    conditions = []
    params = []
    if q:
        conditions.append("""(LOCATE(%s, CONCAT(p.FName, ' ', p.LName)) > 0
                             OR LOCATE(%s, CAST(b.Bk_id AS CHAR)) > 0
                             OR LOCATE(%s, b.Seat_no) > 0 OR LOCATE(%s, b.Flight_id) > 0)""")
        params.extend([q] * 4)
    for column, value in [("b.Status", status), ("b.Flight_id", flight),
                          ("b.Passenger_id", passenger_id), ("b.Bk_id", booking_id)]:
        if value is not None and value != "":
            conditions.append(f"{column} = %s")
            params.append(value)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    return fetch_all(BOOKING_SELECT + where + " ORDER BY b.BookingDate DESC, b.Bk_id DESC", tuple(params))


def find_passengers(q="", passenger_id=None):
    # Count bookings before joining phones. A passenger with two phone numbers
    # must still have each booking counted just once.
    sql = """
        SELECT p.Passenger_id AS passenger_id, p.FName AS first_name, p.LName AS last_name,
               CONCAT(p.FName, ' ', p.LName) AS name, p.Email AS email, ph.Phone AS phone,
               COALESCE(counts.confirmed, 0) AS confirmed
        FROM PASSENGER p
        LEFT JOIN (
            SELECT Passenger_id, COUNT(*) AS confirmed
            FROM BOOKING WHERE Status = 'Confirmed' GROUP BY Passenger_id
        ) counts ON counts.Passenger_id = p.Passenger_id
        LEFT JOIN PASSENGER_PHONE ph ON ph.Passenger_id = p.Passenger_id
    """
    params = ()
    if passenger_id is not None:
        sql += " WHERE p.Passenger_id = %s"
        params = (passenger_id,)
    elif q:
        sql += """
            WHERE LOCATE(%s, CONCAT(p.FName, ' ', p.LName)) > 0 OR LOCATE(%s, p.Email) > 0
               OR LOCATE(%s, CAST(p.Passenger_id AS CHAR)) > 0
               OR EXISTS (SELECT 1 FROM PASSENGER_PHONE matched
                          WHERE matched.Passenger_id = p.Passenger_id AND LOCATE(%s, matched.Phone) > 0)
        """
        params = (q,) * 4
    rows = fetch_all(sql + " ORDER BY p.LName, p.FName, p.Passenger_id, ph.Phone", params)
    passengers = {}
    for row in rows:
        phone = row.pop("phone")
        passenger = passengers.setdefault(row["passenger_id"], {**row, "phones": []})
        if phone is not None:
            passenger["phones"].append(phone)
    return list(passengers.values())


def lock_id_allocation(cursor, relation):
    # These primary keys are assigned by the application (no AUTO_INCREMENT).
    # All application writers for a relation serialize MAX(id)+1, including
    # when the table is empty. Closing this dedicated connection releases the
    # advisory lock AFTER commit or rollback, including on error.
    cursor.execute("""
        SELECT GET_LOCK(CONCAT('AeroManage.', MD5(DATABASE()), '.', %s), 5) AS acquired
    """, (relation,))
    if cursor.fetchone()["acquired"] != 1:
        raise FormProblem("Another record is being saved. Please try again.")


def create_booking(data: BookingInput) -> int:
    try:
        with transaction() as cursor:
            lock_id_allocation(cursor, "BOOKING")
            cursor.execute("""
                SELECT m.Capacity AS capacity FROM FLIGHT_SCHEDULE f
                JOIN AIRCRAFT a ON a.Ac_id = f.Ac_id
                JOIN AIRCRAFT_MODEL m ON m.Model_ID = a.Model_ID
                WHERE f.Flight_id = %s FOR UPDATE
            """, (data.flight_id,))
            flight = cursor.fetchone()
            if flight is None:
                raise FormProblem("Select an existing flight.", 422)
            cursor.execute("SELECT Passenger_id FROM PASSENGER WHERE Passenger_id = %s FOR SHARE",
                           (data.passenger_id,))
            if cursor.fetchone() is None:
                raise FormProblem("Select a registered passenger.", 422)
            cursor.execute("SELECT Tkt_id FROM TICKET WHERE Tkt_id = %s FOR SHARE", (data.ticket_id,))
            if cursor.fetchone() is None:
                raise FormProblem("Select a ticket from the catalogue.", 422)

            # The unique key includes pending AND cancelled bookings. Every
            # existing row therefore holds a distinct seat label on this flight.
            cursor.execute("""
                SELECT COUNT(*) AS held, COUNT(CASE WHEN Seat_no = %s THEN 1 END) AS seat_taken
                FROM BOOKING WHERE Flight_id = %s
            """, (data.seat_no, data.flight_id))
            seats = cursor.fetchone()
            if seats["seat_taken"]:
                raise FormProblem("This seat already has a booking record. Choose a different seat.")
            if seats["held"] >= flight["capacity"]:
                raise FormProblem("All seat allocations on this flight have been used.")
            cursor.execute("SELECT COALESCE(MAX(Bk_id), 0) + 1 AS next_id FROM BOOKING")
            booking_id = cursor.fetchone()["next_id"]
            cursor.execute("""
                INSERT INTO BOOKING
                    (Bk_id, Tkt_id, Passenger_id, Flight_id, Seat_no, BookingDate, Status, PaymentMethod, AmountPaid)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s)
            """, (booking_id, data.ticket_id, data.passenger_id, data.flight_id, data.seat_no,
                  data.status, data.payment_method, data.amount_paid))
            return booking_id
    except IntegrityError as error:
        if error.errno == 1062:
            raise FormProblem("The seat or booking ID was allocated while saving. Check the flight and retry.") from error
        raise


def cancel_booking(booking_id: int):
    with transaction() as cursor:
        cursor.execute("SELECT Status AS status FROM BOOKING WHERE Bk_id = %s FOR UPDATE", (booking_id,))
        booking = cursor.fetchone()
        if booking is None:
            raise FormProblem("This booking could not be found.", 404)
        if booking["status"].casefold() != "cancelled":
            # Keep original amount and seat for the booking history. Revenue
            # queries select confirmed rows, so cancellation removes its revenue.
            cursor.execute("UPDATE BOOKING SET Status = 'Cancelled' WHERE Bk_id = %s", (booking_id,))


def insert_phones(cursor, passenger_id, phones):
    if phones:
        cursor.executemany("INSERT INTO PASSENGER_PHONE (Passenger_id, Phone) VALUES (%s, %s)",
                           [(passenger_id, phone) for phone in phones])


def register_passenger(data: PassengerInput) -> int:
    try:
        with transaction() as cursor:
            lock_id_allocation(cursor, "PASSENGER")
            cursor.execute("SELECT COALESCE(MAX(Passenger_id), 0) + 1 AS next_id FROM PASSENGER")
            passenger_id = cursor.fetchone()["next_id"]
            cursor.execute("INSERT INTO PASSENGER (Passenger_id, FName, LName, Email) VALUES (%s, %s, %s, %s)",
                           (passenger_id, data.first_name, data.last_name, data.email))
            insert_phones(cursor, passenger_id, data.phones)
            return passenger_id
    except IntegrityError as error:
        if error.errno == 1062:
            raise FormProblem("A passenger ID, email address or contact number conflicts with an existing record. Check the details and retry.") from error
        raise


def update_contact(passenger_id: int, data: ContactInput):
    try:
        with transaction() as cursor:
            cursor.execute("SELECT Passenger_id FROM PASSENGER WHERE Passenger_id = %s FOR UPDATE", (passenger_id,))
            if cursor.fetchone() is None:
                raise FormProblem("This passenger could not be found.", 404)
            cursor.execute("UPDATE PASSENGER SET Email = %s WHERE Passenger_id = %s", (data.email, passenger_id))
            cursor.execute("DELETE FROM PASSENGER_PHONE WHERE Passenger_id = %s", (passenger_id,))
            insert_phones(cursor, passenger_id, data.phones)
    except IntegrityError as error:
        if error.errno == 1062:
            raise FormProblem("Check for an email already in use or a duplicate number in this passenger’s contacts.") from error
        raise
