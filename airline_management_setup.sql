-- Airline Management System | MySQL 8.0+
-- Based on the 14-relation normalized schema supplied in the project PDF.
-- WARNING: Running this script resets only the airline_management database.
DROP DATABASE IF EXISTS airline_management;
CREATE DATABASE airline_management CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE airline_management;

-- 1. COUNTRY
CREATE TABLE COUNTRY (
  Country_ID INT PRIMARY KEY,
  Country_Name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. CITY
CREATE TABLE CITY (
  City_ID INT PRIMARY KEY,
  City_Name VARCHAR(100) NOT NULL,
  Country_ID INT NOT NULL,
  CONSTRAINT fk_city_country FOREIGN KEY (Country_ID) REFERENCES COUNTRY(Country_ID),
  CONSTRAINT uq_city_country UNIQUE (City_Name, Country_ID)
);

-- 3. AIRPORT
CREATE TABLE AIRPORT (
  Airport_code VARCHAR(10) PRIMARY KEY,
  Airport_name VARCHAR(150) NOT NULL,
  City_ID INT NOT NULL,
  CONSTRAINT fk_airport_city FOREIGN KEY (City_ID) REFERENCES CITY(City_ID)
);

-- 4. AIRLINE
CREATE TABLE AIRLINE (
  Airline_ID INT PRIMARY KEY,
  Airline_Name VARCHAR(100) NOT NULL UNIQUE
);

-- 5. AIRCRAFT_MODEL
CREATE TABLE AIRCRAFT_MODEL (
  Model_ID INT PRIMARY KEY,
  Model_Name VARCHAR(100) NOT NULL UNIQUE,
  Capacity INT NOT NULL,
  Weight DECIMAL(12,2) NOT NULL COMMENT 'Weight in kilograms (sample reference value)',
  CONSTRAINT chk_model_capacity CHECK (Capacity > 0),
  CONSTRAINT chk_model_weight CHECK (Weight > 0)
);

-- 6. AIRCRAFT
CREATE TABLE AIRCRAFT (
  Ac_id VARCHAR(40) PRIMARY KEY,
  Airline_ID INT NOT NULL,
  Model_ID INT NOT NULL,
  Airport_code VARCHAR(10) NOT NULL,
  CONSTRAINT fk_aircraft_airline FOREIGN KEY (Airline_ID) REFERENCES AIRLINE(Airline_ID),
  CONSTRAINT fk_aircraft_model FOREIGN KEY (Model_ID) REFERENCES AIRCRAFT_MODEL(Model_ID),
  CONSTRAINT fk_aircraft_airport FOREIGN KEY (Airport_code) REFERENCES AIRPORT(Airport_code),
  CONSTRAINT chk_aircraft_id_airport CHECK (
    LEFT(Ac_id, CHAR_LENGTH(Airport_code)) = Airport_code
    AND RIGHT(Ac_id, CHAR_LENGTH(Airport_code)) = Airport_code
  )
);

-- 7. ADMIN
CREATE TABLE ADMIN (
  Admin_id INT PRIMARY KEY,
  Airport_code VARCHAR(10) NOT NULL,
  FName VARCHAR(60) NOT NULL,
  LName VARCHAR(60) NOT NULL,
  Email VARCHAR(150) NOT NULL UNIQUE,
  Phone VARCHAR(20),
  Addr_Street VARCHAR(150),
  Addr_City VARCHAR(100),
  Addr_State VARCHAR(100),
  Addr_Pincode VARCHAR(12),
  DateOfBirth DATE,
  CONSTRAINT fk_admin_airport FOREIGN KEY (Airport_code) REFERENCES AIRPORT(Airport_code)
);

-- 8. CREW_STAFF
CREATE TABLE CREW_STAFF (
  Staff_id INT PRIMARY KEY,
  Airport_code VARCHAR(10) NOT NULL,
  FName VARCHAR(60) NOT NULL,
  LName VARCHAR(60) NOT NULL,
  Designation VARCHAR(80) NOT NULL,
  Gender VARCHAR(20),
  Email VARCHAR(150) NOT NULL UNIQUE,
  Phone VARCHAR(20),
  Addr_Street VARCHAR(150),
  Addr_City VARCHAR(100),
  Addr_State VARCHAR(100),
  Addr_Pincode VARCHAR(12),
  CONSTRAINT fk_crew_airport FOREIGN KEY (Airport_code) REFERENCES AIRPORT(Airport_code)
);

-- 9. FLIGHT_SCHEDULE
CREATE TABLE FLIGHT_SCHEDULE (
  Flight_id VARCHAR(15) PRIMARY KEY,
  Ac_id VARCHAR(40) NOT NULL,
  Admin_id INT NOT NULL,
  Dep_Airport_code VARCHAR(10) NOT NULL,
  Arr_Airport_code VARCHAR(10) NOT NULL,
  DepartureTime DATETIME NOT NULL,
  ArrivalTime DATETIME NOT NULL,
  CONSTRAINT fk_flight_aircraft FOREIGN KEY (Ac_id) REFERENCES AIRCRAFT(Ac_id),
  CONSTRAINT fk_flight_admin FOREIGN KEY (Admin_id) REFERENCES ADMIN(Admin_id),
  CONSTRAINT fk_flight_departure FOREIGN KEY (Dep_Airport_code) REFERENCES AIRPORT(Airport_code),
  CONSTRAINT fk_flight_arrival FOREIGN KEY (Arr_Airport_code) REFERENCES AIRPORT(Airport_code),
  CONSTRAINT chk_flight_different_airports CHECK (Dep_Airport_code <> Arr_Airport_code),
  CONSTRAINT chk_flight_times CHECK (ArrivalTime > DepartureTime)
);

-- 10. STAFF_ASSIGNMENT
CREATE TABLE STAFF_ASSIGNMENT (
  Assignment_id INT PRIMARY KEY,
  Flight_id VARCHAR(15) NOT NULL,
  Staff_id INT NOT NULL,
  Role VARCHAR(10) NOT NULL,
  AssignmentDate DATE NOT NULL,
  CONSTRAINT fk_assignment_flight FOREIGN KEY (Flight_id) REFERENCES FLIGHT_SCHEDULE(Flight_id),
  CONSTRAINT fk_assignment_staff FOREIGN KEY (Staff_id) REFERENCES CREW_STAFF(Staff_id),
  CONSTRAINT uq_assignment_flight_staff UNIQUE (Flight_id, Staff_id),
  CONSTRAINT chk_assignment_role CHECK (Role IN ('Flying', 'Standby'))
);

-- 11. PASSENGER
CREATE TABLE PASSENGER (
  Passenger_id INT PRIMARY KEY,
  FName VARCHAR(60) NOT NULL,
  LName VARCHAR(60) NOT NULL,
  Gender VARCHAR(20),
  CNIC VARCHAR(25) UNIQUE,
  Passport VARCHAR(25) UNIQUE,
  DateOfBirth DATE,
  Email VARCHAR(150) NOT NULL UNIQUE,
  Addr_Street VARCHAR(150),
  Addr_City VARCHAR(100),
  Addr_State VARCHAR(100),
  Addr_Pincode VARCHAR(12)
);

-- 12. PASSENGER_PHONE
CREATE TABLE PASSENGER_PHONE (
  Passenger_id INT NOT NULL,
  Phone VARCHAR(20) NOT NULL,
  PRIMARY KEY (Passenger_id, Phone),
  CONSTRAINT fk_phone_passenger FOREIGN KEY (Passenger_id) REFERENCES PASSENGER(Passenger_id)
);

-- 13. TICKET
CREATE TABLE TICKET (
  Tkt_id INT PRIMARY KEY,
  Class VARCHAR(30) NOT NULL,
  Price DECIMAL(10,2) NOT NULL,
  Student_Discount DECIMAL(5,2) NOT NULL DEFAULT 0 COMMENT 'Percentage discount (0-100)',
  Extra_Luggage BOOLEAN NOT NULL DEFAULT FALSE,
  Flexible_Ticket BOOLEAN NOT NULL DEFAULT FALSE,
  Meals BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT chk_ticket_price CHECK (Price >= 0),
  CONSTRAINT chk_ticket_student_discount CHECK (Student_Discount BETWEEN 0 AND 100)
);

-- 14. BOOKING
CREATE TABLE BOOKING (
  Bk_id INT PRIMARY KEY,
  Tkt_id INT NOT NULL,
  Passenger_id INT NOT NULL,
  Flight_id VARCHAR(15) NOT NULL,
  Seat_no VARCHAR(8) NOT NULL,
  BookingDate DATE NOT NULL,
  Status VARCHAR(30) NOT NULL,
  PaymentMethod VARCHAR(30) NOT NULL,
  AmountPaid DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_booking_ticket FOREIGN KEY (Tkt_id) REFERENCES TICKET(Tkt_id),
  CONSTRAINT fk_booking_passenger FOREIGN KEY (Passenger_id) REFERENCES PASSENGER(Passenger_id),
  CONSTRAINT fk_booking_flight FOREIGN KEY (Flight_id) REFERENCES FLIGHT_SCHEDULE(Flight_id),
  CONSTRAINT uq_booking_flight_seat UNIQUE (Flight_id, Seat_no),
  CONSTRAINT chk_booking_amount CHECK (AmountPaid >= 0)
);

-- SAMPLE DATA (fictional; for demonstrating the project queries)
INSERT INTO COUNTRY VALUES
(1,'India'), (2,'United Arab Emirates'), (3,'Singapore');

INSERT INTO CITY VALUES
(1,'Delhi',1), (2,'Mumbai',1), (3,'Bengaluru',1),
(4,'Chandigarh',1), (5,'Dubai',2), (6,'Singapore',3);

INSERT INTO AIRPORT VALUES
('DEL','Indira Gandhi International Airport',1),
('BOM','Chhatrapati Shivaji Maharaj International Airport',2),
('BLR','Kempegowda International Airport',3),
('IXC','Shaheed Bhagat Singh International Airport',4),
('DXB','Dubai International Airport',5),
('SIN','Singapore Changi Airport',6);

INSERT INTO AIRLINE VALUES
(1,'Air India'), (2,'IndiGo'), (3,'Emirates');

-- Weight entries are illustrative, not certified manufacturer values.
INSERT INTO AIRCRAFT_MODEL VALUES
(1,'Airbus A320neo',180,44500.00),
(2,'Boeing 737-800',189,41400.00),
(3,'Boeing 777-300ER',396,167800.00);

INSERT INTO AIRCRAFT VALUES
('DEL-AI101-DEL',1,1,'DEL'),
('BOM-IG202-BOM',2,1,'BOM'),
('BLR-IG303-BLR',2,2,'BLR'),
('DXB-EK404-DXB',3,3,'DXB'),
('IXC-AI505-IXC',1,1,'IXC');

INSERT INTO ADMIN VALUES
(101,'DEL','Aditi','Sharma','aditi.sharma@example.com','9000000101','Sector 10','Delhi','Delhi','110001','1988-04-12'),
(102,'BOM','Rohan','Mehta','rohan.mehta@example.com','9000000102','Andheri East','Mumbai','Maharashtra','400069','1985-07-25'),
(103,'BLR','Neha','Rao','neha.rao@example.com','9000000103','MG Road','Bengaluru','Karnataka','560001','1990-11-03'),
(104,'DXB','Sara','Khan','sara.khan@example.com','9000000104','Terminal Road','Dubai','Dubai','000000','1987-01-19');

INSERT INTO CREW_STAFF VALUES
(201,'DEL','Arjun','Singh','Pilot','Male','arjun.singh@example.com','9000000201','Janpath','Delhi','Delhi','110001'),
(202,'DEL','Priya','Kapoor','Cabin Crew','Female','priya.kapoor@example.com','9000000202','Karol Bagh','Delhi','Delhi','110005'),
(203,'BOM','Karan','Patel','Pilot','Male','karan.patel@example.com','9000000203','Bandra','Mumbai','Maharashtra','400050'),
(204,'BLR','Isha','Nair','Cabin Crew','Female','isha.nair@example.com','9000000204','Indiranagar','Bengaluru','Karnataka','560038'),
(205,'DXB','Omar','Ali','Pilot','Male','omar.ali@example.com','9000000205','Deira','Dubai','Dubai','000000'),
(206,'IXC','Meera','Sethi','Cabin Crew','Female','meera.sethi@example.com','9000000206','Sector 17','Chandigarh','Chandigarh','160017');

INSERT INTO FLIGHT_SCHEDULE VALUES
('AI101','DEL-AI101-DEL',101,'DEL','BOM','2026-11-12 08:00:00','2026-11-12 10:15:00'),
('6E202','BOM-IG202-BOM',102,'BOM','BLR','2026-11-12 12:00:00','2026-11-12 13:50:00'),
('6E303','BLR-IG303-BLR',103,'BLR','DEL','2026-11-13 06:30:00','2026-11-13 09:15:00'),
('EK404','DXB-EK404-DXB',104,'DXB','DEL','2026-11-14 09:00:00','2026-11-14 13:30:00'),
('AI505','IXC-AI505-IXC',101,'IXC','DEL','2026-11-15 15:00:00','2026-11-15 16:10:00'),
('AI106','DEL-AI101-DEL',101,'DEL','BOM','2026-11-16 18:00:00','2026-11-16 20:15:00'),
('6E207','BOM-IG202-BOM',102,'BOM','DEL','2026-11-17 07:30:00','2026-11-17 09:45:00');

INSERT INTO STAFF_ASSIGNMENT VALUES
(1,'AI101',201,'Flying','2026-11-10'),
(2,'AI101',202,'Flying','2026-11-10'),
(3,'AI101',206,'Standby','2026-11-10'),
(4,'6E202',203,'Flying','2026-11-10'),
(5,'6E202',204,'Standby','2026-11-10'),
(6,'6E303',203,'Flying','2026-11-11'),
(7,'6E303',204,'Flying','2026-11-11'),
(8,'EK404',205,'Flying','2026-11-12'),
(9,'AI505',201,'Flying','2026-11-13'),
(10,'AI505',206,'Flying','2026-11-13'),
(11,'AI106',201,'Flying','2026-11-14'),
(12,'AI106',202,'Standby','2026-11-14'),
(13,'6E207',203,'Flying','2026-11-15');

INSERT INTO PASSENGER VALUES
(301,'Utkarsh','Gupta','Male',NULL,'P0000001','2006-02-10','utkarsh.demo@example.com','Model Town','Patiala','Punjab','147001'),
(302,'Ritika','Saxena','Female',NULL,'P0000002','2005-06-08','ritika.demo@example.com','Sector 22','Chandigarh','Chandigarh','160022'),
(303,'Baani','Singh','Female',NULL,'P0000003','2005-08-14','baani.demo@example.com','Sector 35','Chandigarh','Chandigarh','160035'),
(304,'Dev','Malhotra','Male',NULL,'P0000004','1999-12-01','dev.demo@example.com','Powai','Mumbai','Maharashtra','400076'),
(305,'Ananya','Iyer','Female',NULL,'P0000005','2001-03-22','ananya.demo@example.com','Koramangala','Bengaluru','Karnataka','560034'),
(306,'Kabir','Sood','Male',NULL,'P0000006','1996-09-05','kabir.demo@example.com','Sector 8','Delhi','Delhi','110008'),
(307,'Zoya','Ahmed','Female',NULL,'P0000007','2000-10-17','zoya.demo@example.com','Civil Lines','Delhi','Delhi','110054'),
(308,'Aman','Verma','Male',NULL,'P0000008','2002-05-29','aman.demo@example.com','Sector 15','Chandigarh','Chandigarh','160015');

INSERT INTO PASSENGER_PHONE VALUES
(301,'9000000301'), (301,'9000000391'),
(302,'9000000302'), (303,'9000000303'), (304,'9000000304'),
(305,'9000000305'), (306,'9000000306'), (307,'9000000307');

INSERT INTO TICKET VALUES
(401,'Economy',4500.00,10.00,0,0,0),
(402,'Economy',5200.00,0.00,1,0,1),
(403,'Business',18500.00,0.00,1,1,1),
(404,'Economy',6800.00,5.00,0,1,1),
(405,'Premium Economy',9200.00,0.00,1,1,1),
(406,'Economy',3900.00,0.00,0,0,0);

INSERT INTO BOOKING VALUES
(501,401,301,'AI101','12A','2026-11-04','Confirmed','UPI',4050.00),
(502,402,302,'AI101','12B','2026-11-04','Confirmed','Card',5500.00),
(503,401,303,'AI101','12C','2026-11-05','Confirmed','UPI',4050.00),
(504,403,304,'6E202','2A','2026-11-05','Confirmed','Card',19500.00),
(505,405,305,'6E202','7A','2026-11-06','Confirmed','Net Banking',9600.00),
(506,404,306,'6E303','10A','2026-11-06','Confirmed','UPI',6460.00),
(507,403,307,'EK404','3A','2026-11-07','Confirmed','Card',21500.00),
(508,406,308,'AI505','15C','2026-11-07','Confirmed','UPI',3900.00),
(509,402,301,'AI106','14A','2026-11-08','Confirmed','UPI',5200.00),
(510,401,302,'AI106','14B','2026-11-08','Cancelled','Card',0.00),
(511,405,303,'6E303','9B','2026-11-09','Confirmed','Card',9500.00);

-- Verification: Should show 14 tables.
SHOW TABLES;

-- Verification: Table population (each count is an actual count from demo data).
SELECT 'COUNTRY' AS Table_Name, COUNT(*) AS Record_Count FROM COUNTRY
UNION ALL SELECT 'CITY', COUNT(*) FROM CITY
UNION ALL SELECT 'AIRPORT', COUNT(*) FROM AIRPORT
UNION ALL SELECT 'AIRLINE', COUNT(*) FROM AIRLINE
UNION ALL SELECT 'AIRCRAFT_MODEL', COUNT(*) FROM AIRCRAFT_MODEL
UNION ALL SELECT 'AIRCRAFT', COUNT(*) FROM AIRCRAFT
UNION ALL SELECT 'ADMIN', COUNT(*) FROM ADMIN
UNION ALL SELECT 'CREW_STAFF', COUNT(*) FROM CREW_STAFF
UNION ALL SELECT 'FLIGHT_SCHEDULE', COUNT(*) FROM FLIGHT_SCHEDULE
UNION ALL SELECT 'STAFF_ASSIGNMENT', COUNT(*) FROM STAFF_ASSIGNMENT
UNION ALL SELECT 'PASSENGER', COUNT(*) FROM PASSENGER
UNION ALL SELECT 'PASSENGER_PHONE', COUNT(*) FROM PASSENGER_PHONE
UNION ALL SELECT 'TICKET', COUNT(*) FROM TICKET
UNION ALL SELECT 'BOOKING', COUNT(*) FROM BOOKING;
