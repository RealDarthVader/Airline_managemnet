"""Read-only SQL for the flight schedule and its supporting directories."""

# Aggregate bookings first, so adding an aircraft or airport join never counts a
# seat twice. A flight without bookings has no matching totals row.
FLIGHT_SUMMARY = """
    SELECT f.Flight_id AS flight_id, a.Ac_id AS aircraft_id,
           al.Airline_ID AS airline_id, al.Airline_Name AS airline,
           m.Model_Name AS model, m.Capacity AS capacity,
           dep.City_ID AS source_id, arr.City_ID AS destination_id,
           origin.City_Name AS source_city, destination.City_Name AS destination_city,
           dep.Airport_code AS dep_code, arr.Airport_code AS arr_code,
           dep.Airport_name AS dep_airport, arr.Airport_name AS arr_airport,
           f.DepartureTime AS departure_time, f.ArrivalTime AS arrival_time,
           COALESCE(b.confirmed, 0) AS booked_seats,
           COALESCE(b.allocated, 0) AS allocated_seats,
           GREATEST(m.Capacity - COALESCE(b.allocated, 0), 0) AS available_seats,
           ROUND(COALESCE(b.confirmed, 0) * 100.0 / m.Capacity, 2) AS occupancy,
           COALESCE(b.revenue, 0) AS revenue
    FROM FLIGHT_SCHEDULE AS f
    JOIN AIRCRAFT AS a ON a.Ac_id = f.Ac_id
    JOIN AIRLINE AS al ON al.Airline_ID = a.Airline_ID
    JOIN AIRCRAFT_MODEL AS m ON m.Model_ID = a.Model_ID
    JOIN AIRPORT AS dep ON dep.Airport_code = f.Dep_Airport_code
    JOIN CITY AS origin ON origin.City_ID = dep.City_ID
    JOIN AIRPORT AS arr ON arr.Airport_code = f.Arr_Airport_code
    JOIN CITY AS destination ON destination.City_ID = arr.City_ID
    LEFT JOIN (
        SELECT Flight_id,
               COUNT(*) AS allocated,
               SUM(CASE WHEN Status = 'Confirmed' THEN 1 ELSE 0 END) AS confirmed,
               SUM(CASE WHEN Status = 'Confirmed' THEN AmountPaid ELSE 0 END) AS revenue
        FROM BOOKING
        GROUP BY Flight_id
    ) AS b ON b.Flight_id = f.Flight_id
"""

CITIES = """
    SELECT c.City_ID AS value, CONCAT(c.City_Name, ', ', n.Country_Name) AS label
    FROM CITY AS c
    JOIN COUNTRY AS n ON n.Country_ID = c.Country_ID
    ORDER BY c.City_Name, n.Country_Name
"""
AIRLINES = "SELECT Airline_ID AS value, Airline_Name AS label FROM AIRLINE ORDER BY Airline_Name"
FLIGHT_IDS = "SELECT Flight_id AS value, Flight_id AS label FROM FLIGHT_SCHEDULE ORDER BY Flight_id"
DESIGNATIONS = "SELECT DISTINCT Designation AS value, Designation AS label FROM CREW_STAFF ORDER BY Designation"
COUNTRIES = "SELECT Country_ID AS value, Country_Name AS label FROM COUNTRY ORDER BY Country_Name"

AIRCRAFT = """
    SELECT a.Ac_id AS aircraft_id, al.Airline_Name AS airline, m.Model_Name AS model,
           m.Capacity AS capacity, m.Weight AS weight, p.Airport_code AS airport_code,
           p.Airport_name AS airport
    FROM AIRCRAFT AS a
    JOIN AIRLINE AS al ON al.Airline_ID = a.Airline_ID
    JOIN AIRCRAFT_MODEL AS m ON m.Model_ID = a.Model_ID
    JOIN AIRPORT AS p ON p.Airport_code = a.Airport_code
"""

# Keep staff without an assignment visible on the full crew roster.
CREW = """
    SELECT s.Staff_id AS staff_id, CONCAT(s.FName, ' ', s.LName) AS name,
           s.Designation AS designation, sa.Flight_id AS flight_id,
           sa.AssignmentDate AS assigned, sa.Role AS role
    FROM CREW_STAFF AS s
    LEFT JOIN STAFF_ASSIGNMENT AS sa ON sa.Staff_id = s.Staff_id
"""
CREW_ORDER = " ORDER BY s.LName, s.FName, s.Staff_id, sa.AssignmentDate, sa.Flight_id"

TICKETS = """
    SELECT Tkt_id AS ticket_id, Class AS cabin, Price AS fare,
           Student_Discount AS discount, Extra_Luggage AS luggage,
           Flexible_Ticket AS flexible, Meals AS meals
    FROM TICKET
    ORDER BY Price, Tkt_id
"""

AIRPORTS = """
    SELECT p.Airport_code AS code, p.Airport_name AS airport,
           c.City_Name AS city, n.Country_Name AS country
    FROM AIRPORT AS p
    JOIN CITY AS c ON c.City_ID = p.City_ID
    JOIN COUNTRY AS n ON n.Country_ID = c.Country_ID
"""

ADMINISTRATORS = """
    SELECT ad.Admin_id AS admin_id, CONCAT(ad.FName, ' ', ad.LName) AS name,
           ad.Email AS email, ad.Phone AS phone, p.Airport_code AS airport_code,
           p.Airport_name AS airport, f.Flight_id AS flight_id
    FROM ADMIN AS ad
    JOIN AIRPORT AS p ON p.Airport_code = ad.Airport_code
    LEFT JOIN FLIGHT_SCHEDULE AS f ON f.Admin_id = ad.Admin_id
    ORDER BY ad.LName, ad.FName, ad.Admin_id, f.DepartureTime, f.Flight_id
"""

FLIGHT_BOOKINGS = """
    SELECT b.Bk_id AS booking_id, p.Passenger_id AS passenger_id,
           CONCAT(p.FName, ' ', p.LName) AS name, t.Class AS cabin,
           b.Seat_no AS seat, b.BookingDate AS booked, b.Status AS status
    FROM BOOKING AS b
    JOIN PASSENGER AS p ON p.Passenger_id = b.Passenger_id
    JOIN TICKET AS t ON t.Tkt_id = b.Tkt_id
    WHERE b.Flight_id = %s
    ORDER BY b.BookingDate DESC, b.Bk_id DESC
"""


def filtered_query(base, conditions, ordering):
    """Only SQL fragments from the module are interpolated. Values stay bound."""
    active = [(column, value) for column, value in conditions if value not in (None, "")]
    if active:
        base += " WHERE " + " AND ".join(column + " = %s" for column, _ in active)
    return base + ordering, tuple(value for _, value in active)
