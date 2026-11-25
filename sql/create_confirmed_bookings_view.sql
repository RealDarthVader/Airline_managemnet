-- Optional: run manually in MySQL Workbench only if Confirmed_Bookings is missing.
-- This creates the view used by demonstration 17. CREATE VIEW fails if it exists.
-- The application never runs DDL. No table or booking record is changed.
USE airline_management;

CREATE VIEW Confirmed_Bookings AS
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
