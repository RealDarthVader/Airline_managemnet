"""Start locally with: uvicorn main:app --reload"""

import logging
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from mysql.connector import Error as MySQLError
from starlette.exceptions import HTTPException

from routes import analytics, bookings, dashboard, directories, flights, passengers, sql_explorer
from ui import ROOT, render

app = FastAPI(title="AeroManage", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
for module in (dashboard, flights, bookings, passengers, directories, analytics, sql_explorer):
    app.include_router(module.router)


@app.middleware("http")
async def browser_requests(request: Request, call_next):
    # Local HTML forms submit to this origin. Block cross-site browser writes.
    if request.method == "POST":
        source = request.headers.get("origin") or request.headers.get("referer")
        cross_site = request.headers.get("sec-fetch-site") == "cross-site"
        if source:
            origin = urlsplit(source)
            cross_site |= (origin.scheme, origin.netloc) != (request.url.scheme, request.url.netloc)
        if cross_site or not source:
            return render(request, "error.html", title="Form origin could not be verified",
                          message="Open the form in this workspace and submit it again.", status_code=403)
    response = await call_next(request)
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if not request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(MySQLError)
async def database_error(request: Request, error: MySQLError):
    logging.getLogger("uvicorn.error").warning("MySQL request failed (code %s)", error.errno)
    if error.errno in (1045, 1044):
        message = "Check the MySQL username, password and database privileges in your local .env file."
    elif error.errno in (2002, 2003, 2005, 2013):
        message = "Check that the MySQL service is running and that DB_HOST and DB_PORT match your server."
    elif error.errno in (1049, 1054, 1146):
        message = "Check DB_NAME and compare the available tables and columns with the supplied schema."
    else:
        message = "The database could not complete this request. Check the server log for the MySQL error code."
    return render(request, "error.html", title="Database unavailable", message=message, status_code=503)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, error: RequestValidationError):
    return render(request, "error.html", title="Invalid request",
                  message="Check the record identifier or filter value and try again.", status_code=422)


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException):
    return render(request, "error.html", title="Page not found" if error.status_code == 404 else "Request unavailable",
                  message=str(error.detail), status_code=error.status_code)
