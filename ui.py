"""Template setup and presentation helpers shared by every router."""

from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi.templating import Jinja2Templates

from database import settings

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))
NAV = (
    ("Workspace", (("Overview", "/", "grid"),)),
    ("Operations", (
        ("Flights", "/flights", "plane"), ("Bookings", "/bookings", "booking"),
        ("Passengers", "/passengers", "users"), ("Aircraft", "/aircraft", "fleet"),
        ("Crew", "/crew", "crew"), ("Tickets", "/tickets", "ticket"),
        ("Airports", "/airports", "tower"), ("Administrators", "/administrators", "shield"),
    )),
    ("Insights", (("Analytics", "/analytics", "chart"), ("SQL Explorer", "/sql-explorer", "code"))),
)


def money(value):
    return f"₹{value:,.2f}"


templates.env.filters.update(
    money=money,
    money_short=lambda value: f"₹{value:,.0f}" if value == int(value) else money(value),
    initials=lambda name: "".join(part[0] for part in name.split()[:2]).upper(),
    number=lambda value: f"{value:,}",
    datefmt=lambda value: value.strftime("%d %b %Y"),
    datetimefmt=lambda value: value.strftime("%d %b %Y · %H:%M"),
    pathpart=lambda value: quote(str(value), safe=""),
)


def render(request, template, *, title, status_code=200, **context):
    path = "/" + request.url.path.strip("/").split("/")[0]
    section_name = next(
        (label for _, items in NAV for label, href, _ in items if href == path), title
    )
    return templates.TemplateResponse(
        request=request,
        name=template,
        context=dict(
            nav=NAV, active_path=path, section_name=section_name, title=title, status_code=status_code,
            today=date.today(), database_name=settings()["DB_NAME"],
            **context,
        ),
        status_code=status_code,
    )
