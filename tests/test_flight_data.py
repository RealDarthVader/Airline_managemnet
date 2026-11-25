"""Optional integration check against the configured MySQL database (SELECT only)."""

import os
import unittest
from decimal import Decimal, ROUND_HALF_UP

from database import transaction
from operations_sql import FLIGHT_SUMMARY, filtered_query


@unittest.skipUnless(os.getenv("RUN_MYSQL_READ_TESTS") == "1", "Set RUN_MYSQL_READ_TESTS=1 for live SELECT checks")
class FlightDataTests(unittest.TestCase):
    def test_capacity_revenue_and_occupancy_against_booking_records(self):
        with transaction() as cursor:
            cursor.execute("SELECT Flight_id FROM FLIGHT_SCHEDULE")
            flight_ids = {r["Flight_id"] for r in cursor.fetchall()}
            cursor.execute("""
                SELECT f.Flight_id, b.Status = 'Confirmed' AS confirmed, b.AmountPaid
                FROM BOOKING AS b JOIN FLIGHT_SCHEDULE AS f ON f.Flight_id = b.Flight_id
            """)
            bookings = cursor.fetchall()
            cursor.execute(FLIGHT_SUMMARY)
            summaries = cursor.fetchall()
        self.assertEqual({f["flight_id"] for f in summaries}, flight_ids)
        self.assertEqual(len(summaries), len(flight_ids))
        for flight in summaries:
            with self.subTest(flight=flight["flight_id"]):
                allocated = [r for r in bookings if r["Flight_id"] == flight["flight_id"]]
                confirmed = [r for r in allocated if r["confirmed"]]
                occupancy = Decimal(100 * len(confirmed)) / flight["capacity"]
                self.assertEqual(flight["booked_seats"], len(confirmed))
                self.assertEqual(flight["available_seats"], max(flight["capacity"] - len(allocated), 0))
                self.assertEqual(flight["occupancy"], occupancy.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                self.assertEqual(flight["revenue"], sum(r["AmountPaid"] for r in confirmed))

    def test_city_pair_filters(self):
        with transaction() as cursor:
            cursor.execute(FLIGHT_SUMMARY)
            schedule = cursor.fetchall()
            if not schedule:
                self.skipTest("No scheduled flights")
            source = schedule[0]["source_id"]
            destination = schedule[0]["destination_id"]
            query, params = filtered_query(
                FLIGHT_SUMMARY, [("dep.City_ID", source), ("arr.City_ID", destination)], "",
            )
            cursor.execute(query, params)
            matching = cursor.fetchall()
        expected = {f["flight_id"] for f in schedule if f["source_id"] == source and f["destination_id"] == destination}
        self.assertEqual({f["flight_id"] for f in matching}, expected)
