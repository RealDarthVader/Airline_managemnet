from time import perf_counter

from fastapi import APIRouter, HTTPException, Request
from mysql.connector import Error as MySQLError

from database import transaction
from explorer_queries import DEMOS, VIEW_DEFINITION, sql_tokens
from ui import render


router = APIRouter(prefix="/sql-explorer")


@router.get("")
def sql_explorer(request: Request, query: int = 1, run: bool = False):
    demo = DEMOS.get(query)
    if demo is None:
        raise HTTPException(status_code=404, detail="This SQL demonstration does not exist.")

    rows = None
    columns = ()
    elapsed_ms = None
    missing_view = False
    if run:
        try:
            with transaction() as cursor:
                # Only a catalog ID comes from the request. There is no user SQL.
                start = perf_counter()
                cursor.execute(demo.sql)
                rows = cursor.fetchall()
                elapsed_ms = (perf_counter() - start) * 1000
                columns = cursor.column_names
        except MySQLError as exc:
            if query == 17 and exc.errno == 1146:
                missing_view = True
            else:
                raise  # The app-wide handler reports connection and database errors.

    return render(request, "sql_explorer.html", title="SQL Explorer", demos=DEMOS.values(),
                  demo=demo, tokens=sql_tokens(demo.sql + ";"),
                  definition_tokens=sql_tokens(VIEW_DEFINITION + ";"), rows=rows,
                  columns=columns, elapsed_ms=elapsed_ms, missing_view=missing_view)
