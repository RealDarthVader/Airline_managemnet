USE airline_management;
SHOW TABLES;
SELECT
    F.Flight_id,
    A1.Airport_name AS Departure_Airport,
    A2.Airport_name AS Arrival_Airport,
    F.DepartureTime,
    F.ArrivalTime
FROM FLIGHT_SCHEDULE F
JOIN AIRPORT A1
    ON F.Dep_Airport_code = A1.Airport_code
JOIN AIRPORT A2
    ON F.Arr_Airport_code = A2.Airport_code
ORDER BY F.DepartureTime;
SELECT
    B.Bk_id,
    CONCAT(P.FName, ' ', P.LName)
        AS Passenger_Name,
    B.Flight_id,
    B.Seat_no,
    B.BookingDate,
    B.Status,
    B.AmountPaid
FROM BOOKING B
JOIN PASSENGER P
    ON B.Passenger_id = P.Passenger_id
ORDER BY B.BookingDate DESC;
SELECT
    F.Flight_id,
    C1.City_Name AS Source_City,
    C2.City_Name AS Destination_City,
    F.DepartureTime,
    F.ArrivalTime
FROM FLIGHT_SCHEDULE F
JOIN AIRPORT A1
    ON F.Dep_Airport_code = A1.Airport_code
JOIN CITY C1
    ON A1.City_ID = C1.City_ID
JOIN AIRPORT A2
    ON F.Arr_Airport_code = A2.Airport_code
JOIN CITY C2
    ON A2.City_ID = C2.City_ID
WHERE C1.City_Name = 'Delhi'
  AND C2.City_Name = 'Mumbai'
ORDER BY F.DepartureTime;
SELECT
    A.Ac_id,
    AL.Airline_Name,
    M.Model_Name,
    M.Capacity,
    M.Weight,
    A.Airport_code
FROM AIRCRAFT A
JOIN AIRLINE AL
    ON A.Airline_ID = AL.Airline_ID
JOIN AIRCRAFT_MODEL M
    ON A.Model_ID = M.Model_ID;
    SELECT
    S.Staff_id,
    CONCAT(S.FName, ' ', S.LName)
        AS Staff_Name,
    S.Designation,
    SA.Flight_id,
    SA.Role,
    SA.AssignmentDate
FROM CREW_STAFF S
JOIN STAFF_ASSIGNMENT SA
    ON S.Staff_id = SA.Staff_id
ORDER BY SA.Flight_id, SA.Role;
SELECT
    Tkt_id,
    Class,
    Price AS Base_Fare,
    Student_Discount,
    Extra_Luggage,
    Flexible_Ticket,
    Meals
FROM TICKET
ORDER BY Price;
SELECT
    F.Flight_id,
    COUNT(B.Bk_id) AS Total_Bookings,
    SUM(B.AmountPaid) AS Total_Revenue
FROM FLIGHT_SCHEDULE F
JOIN BOOKING B
    ON F.Flight_id = B.Flight_id
WHERE B.Status = 'Confirmed'
GROUP BY F.Flight_id
ORDER BY Total_Revenue DESC;
SELECT
    A.Airport_code,
    A.Airport_name,
    C.City_Name,
    CO.Country_Name
FROM AIRPORT A
JOIN CITY C
    ON A.City_ID = C.City_ID
JOIN COUNTRY CO
    ON C.Country_ID = CO.Country_ID
ORDER BY CO.Country_Name, C.City_Name;
SELECT
    F.Flight_id,
    COUNT(B.Bk_id) AS Total_Passengers
FROM FLIGHT_SCHEDULE F
LEFT JOIN BOOKING B
    ON F.Flight_id = B.Flight_id
    AND B.Status = 'Confirmed'
GROUP BY F.Flight_id
ORDER BY Total_Passengers DESC;
SELECT
    A.Admin_id,
    CONCAT(A.FName, ' ', A.LName)
        AS Admin_Name,
    F.Flight_id,
    F.DepartureTime,
    F.ArrivalTime
FROM ADMIN A
JOIN FLIGHT_SCHEDULE F
    ON A.Admin_id = F.Admin_id
ORDER BY A.Admin_id, F.DepartureTime;
SELECT
    P.Passenger_id,
    CONCAT(P.FName, ' ', P.LName)
        AS Passenger_Name,
    P.Email,
    PP.Phone
FROM PASSENGER P
LEFT JOIN PASSENGER_PHONE PP
    ON P.Passenger_id = PP.Passenger_id
ORDER BY P.Passenger_id;
SELECT
    F.Flight_id,
    M.Model_Name,
    M.Capacity AS Total_Seats,
    COUNT(B.Bk_id) AS Booked_Seats,
    M.Capacity - COUNT(B.Bk_id)
        AS Available_Seats
FROM FLIGHT_SCHEDULE F
JOIN AIRCRAFT A
    ON F.Ac_id = A.Ac_id
JOIN AIRCRAFT_MODEL M
    ON A.Model_ID = M.Model_ID
LEFT JOIN BOOKING B
    ON F.Flight_id = B.Flight_id
    AND B.Status = 'Confirmed'
GROUP BY
    F.Flight_id,
    M.Model_Name,
    M.Capacity;

SELECT
    P.Passenger_id,
    CONCAT(P.FName, ' ', P.LName) AS Passenger_Name,
    COUNT(B.Bk_id) AS Total_Bookings
FROM PASSENGER P
JOIN BOOKING B
    ON P.Passenger_id = B.Passenger_id
WHERE B.Status = 'Confirmed'
GROUP BY P.Passenger_id, P.FName, P.LName
HAVING COUNT(B.Bk_id) > 1
ORDER BY Total_Bookings DESC;

SELECT
    B.Bk_id,
    CONCAT(P.FName, ' ', P.LName) AS Passenger_Name,
    B.Flight_id,
    B.AmountPaid
FROM BOOKING B
JOIN PASSENGER P
    ON B.Passenger_id = P.Passenger_id
WHERE B.Status = 'Confirmed'
AND B.AmountPaid > (
    SELECT AVG(AmountPaid)
    FROM BOOKING
    WHERE Status = 'Confirmed'
);
SELECT
    F.Flight_id,
    M.Capacity AS Total_Seats,
    COUNT(B.Bk_id) AS Booked_Seats,
    ROUND(
        COUNT(B.Bk_id) * 100.0 / M.Capacity, 2
    ) AS Occupancy_Percentage
FROM FLIGHT_SCHEDULE F
JOIN AIRCRAFT A
    ON F.Ac_id = A.Ac_id
JOIN AIRCRAFT_MODEL M
    ON A.Model_ID = M.Model_ID
LEFT JOIN BOOKING B
    ON F.Flight_id = B.Flight_id
    AND B.Status = 'Confirmed'
GROUP BY F.Flight_id, M.Capacity
ORDER BY Occupancy_Percentage DESC;

SELECT
    AL.Airline_Name,
    COUNT(DISTINCT F.Flight_id) AS Total_Flights,
    COUNT(B.Bk_id) AS Total_Bookings,
    COALESCE(SUM(B.AmountPaid), 0) AS Total_Revenue
FROM AIRLINE AL
JOIN AIRCRAFT A
    ON AL.Airline_ID = A.Airline_ID
JOIN FLIGHT_SCHEDULE F
    ON A.Ac_id = F.Ac_id
LEFT JOIN BOOKING B
    ON F.Flight_id = B.Flight_id
    AND B.Status = 'Confirmed'
GROUP BY AL.Airline_ID, AL.Airline_Name
ORDER BY Total_Revenue DESC;

CREATE OR REPLACE VIEW Confirmed_Bookings AS
SELECT
    B.Bk_id,
    CONCAT(P.FName, ' ', P.LName) AS Passenger_Name,
    B.Flight_id,
    B.Seat_no,
    T.Class,
    B.AmountPaid
FROM BOOKING B
JOIN PASSENGER P
    ON B.Passenger_id = P.Passenger_id
JOIN TICKET T
    ON B.Tkt_id = T.Tkt_id
WHERE B.Status = 'Confirmed';
SELECT * FROM Confirmed_Bookings;