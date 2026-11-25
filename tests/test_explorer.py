"""Read-only checks for the query library and its execution boundary."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from mysql.connector import ProgrammingError
from starlette.requests import Request

from explorer_queries import DEMOS, VIEW_DEFINITION, sql_tokens
from routes.sql_explorer import sql_explorer


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.request = Request({"type": "http", "path": "/sql-explorer", "headers": []})
        # Capturing context keeps these tests independent of a MySQL service.
        render = patch("routes.sql_explorer.render",
                       side_effect=lambda request, template, **context: context)
        render.start()
        self.addCleanup(render.stop)
        db = patch("routes.sql_explorer.transaction")
        self.transaction = db.start()
        self.addCleanup(db.stop)
        self.cursor = self.transaction.return_value.__enter__.return_value

    def test_all_predefined_selects_run_and_highlight_losslessly(self):
        self.assertEqual(list(DEMOS), list(range(1, 18)))
        self.cursor.fetchall.return_value = []
        self.cursor.column_names = ("Flight_id",)
        for number, demo in DEMOS.items():
            with self.subTest(number=number):
                self.assertTrue(demo.sql.upper().startswith("SELECT"))
                self.assertNotIn(";", demo.sql)
                context = sql_explorer(self.request, query=number, run=True)
                self.cursor.execute.assert_called_with(demo.sql)
                self.assertEqual("".join(text for _, text in context["tokens"]), demo.sql + ";")
                self.assertEqual(context["rows"], [])
                self.assertEqual(context["columns"], ("Flight_id",))
                self.assertGreaterEqual(context["elapsed_ms"], 0)

    def test_catalog_is_available_before_connecting(self):
        context = sql_explorer(self.request)
        self.assertIsNone(context["rows"])
        self.transaction.assert_not_called()

    def test_unknown_demo_does_not_connect(self):
        for number in (0, -1, 18):
            with self.assertRaises(HTTPException) as failure:
                sql_explorer(self.request, query=number, run=True)
            self.assertEqual(failure.exception.status_code, 404)
        self.transaction.assert_not_called()

    def test_view_definition_is_for_display_only(self):
        self.cursor.execute.side_effect = ProgrammingError(errno=1146, msg="View missing")
        context = sql_explorer(self.request, query=17, run=True)
        self.assertTrue(context["missing_view"])
        self.assertIsNone(context["rows"])
        self.cursor.execute.assert_called_once_with("SELECT * FROM Confirmed_Bookings")
        self.assertTrue(VIEW_DEFINITION.startswith("CREATE OR REPLACE VIEW"))
        self.assertEqual("".join(text for _, text in sql_tokens(VIEW_DEFINITION)), VIEW_DEFINITION)

    def test_unrelated_database_failure_is_handled_by_the_application(self):
        self.cursor.execute.side_effect = ProgrammingError(errno=1142, msg="Insufficient privileges")
        with self.assertRaises(ProgrammingError):
            sql_explorer(self.request, query=17, run=True)


if __name__ == "__main__":
    unittest.main()
