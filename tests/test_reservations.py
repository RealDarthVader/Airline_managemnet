"""Exercise validation and transaction boundaries without a live database."""

import unittest
from decimal import Decimal
from unittest.mock import patch

from mysql.connector.errors import IntegrityError
from pydantic import ValidationError

import reservation_store as store
from schemas import BookingInput, ContactInput, PassengerInput


def booking_input(**changes):
    values = dict(passenger_id=1, ticket_id=2, flight_id="TEST", seat_no=" 2a ",
                  amount_paid="100.50", payment_method="Card", status="Confirmed")
    return BookingInput.model_validate({**values, **changes})


class ReservationTests(unittest.TestCase):
    def setUp(self):
        # Even a configured local MySQL database receives no queries here.
        connector_patch = patch("database.connect")
        self.connection = connector_patch.start().return_value
        self.addCleanup(connector_patch.stop)
        self.cursor = self.connection.cursor.return_value.__enter__.return_value

    def test_booking_commits_after_checking_flight_references_and_seats(self):
        self.cursor.fetchone.side_effect = [
            {"acquired": 1}, {"capacity": 8}, {"Passenger_id": 1}, {"Tkt_id": 2},
            {"held": 0, "seat_taken": 0}, {"next_id": 1},
        ]
        self.assertEqual(store.create_booking(booking_input()), 1)
        calls = self.cursor.execute.call_args_list
        self.assertIn("GET_LOCK", calls[0].args[0])
        self.assertIn("FOR UPDATE", calls[1].args[0])
        self.assertNotIn("Status", calls[4].args[0])
        self.assertEqual(calls[-1].args[1], (1, 2, 1, "TEST", "2A", "Confirmed", "Card", Decimal("100.50")))
        self.connection.commit.assert_called_once()
        self.connection.close.assert_called_once()

    def test_busy_allocator_never_attempts_an_insert(self):
        self.cursor.fetchone.return_value = {"acquired": 0}
        with self.assertRaisesRegex(store.FormProblem, "being saved"):
            store.create_booking(booking_input())
        self.assertEqual(self.cursor.execute.call_count, 1)
        self.connection.rollback.assert_called_once()

    def test_each_foreign_key_is_checked(self):
        for records, message in [
            ([None], "existing flight"),
            ([{"capacity": 8}, None], "registered passenger"),
            ([{"capacity": 8}, {"Passenger_id": 1}, None], "ticket from the catalogue"),
        ]:
            with self.subTest(message=message):
                self.cursor.fetchone.side_effect = [{"acquired": 1}, *records]
                with self.assertRaisesRegex(store.FormProblem, message):
                    store.create_booking(booking_input())
        self.connection.commit.assert_not_called()
        self.assertEqual(self.connection.rollback.call_count, 3)

    def test_seat_reuse_and_capacity_rejected(self):
        for seats, message in [({"held": 1, "seat_taken": 1}, "already has a booking"),
                               ({"held": 8, "seat_taken": 0}, "All seat allocations")]:
            with self.subTest(seats=seats):
                self.cursor.fetchone.side_effect = [
                    {"acquired": 1}, {"capacity": 8}, {"Passenger_id": 1}, {"Tkt_id": 2}, seats,
                ]
                with self.assertRaisesRegex(store.FormProblem, message):
                    store.create_booking(booking_input())
        self.connection.commit.assert_not_called()
        self.assertEqual(self.connection.rollback.call_count, 2)

    def test_invalid_amounts_rejected_and_zero_accepted(self):
        for amount in ["-1", "NaN", "Infinity", "0.123", "100000000.00", ""]:
            with self.subTest(amount=amount), self.assertRaises(ValidationError):
                booking_input(amount_paid=amount)
        self.assertEqual(booking_input(amount_paid="0.00").amount_paid, 0)

    def test_cancellation_only_changes_status_and_can_be_retried(self):
        self.cursor.fetchone.side_effect = [{"status": "Confirmed"}, {"status": "Cancelled"}]
        store.cancel_booking(1)
        store.cancel_booking(1)
        calls = self.cursor.execute.call_args_list
        self.assertIn("FOR UPDATE", calls[0].args[0])
        self.assertEqual(calls[1].args, ("UPDATE BOOKING SET Status = 'Cancelled' WHERE Bk_id = %s", (1,)))
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.connection.commit.call_count, 2)

    def test_missing_booking_returns_not_found(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaises(store.FormProblem) as caught:
            store.cancel_booking(42)
        self.assertEqual(caught.exception.status_code, 404)
        self.connection.rollback.assert_called_once()

    def test_registration_writes_multiple_phone_rows(self):
        self.cursor.fetchone.side_effect = [{"acquired": 1}, {"next_id": 4}]
        data = PassengerInput(first_name="Alex", last_name="Test", email="a@example.org", phones="100\n200,100")
        self.assertEqual(store.register_passenger(data), 4)
        self.assertEqual(self.cursor.executemany.call_args.args[1], [(4, "100"), (4, "200")])
        self.connection.commit.assert_called_once()

    def test_contact_error_rolls_back_parent_and_phone_changes(self):
        self.cursor.fetchone.return_value = {"Passenger_id": 4}
        self.cursor.executemany.side_effect = IntegrityError(errno=1062)
        with self.assertRaises(store.FormProblem):
            store.update_contact(4, ContactInput(email="a@example.org", phones="100"))
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()
        self.connection.close.assert_called_once()

    def test_search_and_filters_are_bound_parameters(self):
        store.find_bookings("2A", "Pending", "TEST")
        query, params = self.cursor.execute.call_args.args
        self.assertNotIn("2A", query)
        self.assertEqual(params, ("2A", "2A", "2A", "2A", "Pending", "TEST"))

    def test_passenger_directory_retains_all_numbers_and_zero_bookings(self):
        passenger = dict(passenger_id=4, name="Alex Test", first_name="Alex", last_name="Test",
                         email="a@example.org", confirmed=0)
        self.cursor.fetchall.return_value = [{**passenger, "phone": "100"}, {**passenger, "phone": "200"}]
        results = store.find_passengers("100")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["phones"], ["100", "200"])
        self.assertEqual(results[0]["confirmed"], 0)
        self.assertEqual(self.cursor.execute.call_args.args[1], ("100",) * 4)


if __name__ == "__main__":
    unittest.main()
