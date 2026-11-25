"""The 17 predefined MySQL demonstrations in the supplied Project.sql file."""

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Demonstration:
    number: int
    title: str
    requirement: str
    concepts: tuple[str, ...]
    sql: str


# Entries follow the order of the SELECT statements in Project.sql.
CATALOG = (
    ("Flight schedule with airport details",
     "Show each flight’s departure and arrival airports in departure order.",
     ("INNER JOIN", "Table aliases", "ORDER BY")),
    ("Passenger booking details",
     "Match each booking to its passenger and show the seat, payment and booking status.",
     ("INNER JOIN", "CONCAT", "ORDER BY")),
    ("Flights between two cities",
     "Find flights departing Delhi for Mumbai by following each airport’s city relationship.",
     ("Multiple joins", "WHERE", "Table aliases")),
    ("Aircraft and airline information",
     "Match each aircraft to its operator, model, seating capacity, weight and home airport.",
     ("INNER JOIN", "Foreign keys")),
    ("Flight crew assignments",
     "Find the staff working each flight, their designations, assignment dates and flying or standby roles.",
     ("Junction table", "INNER JOIN", "ORDER BY")),
    ("Ticket fares and additional services",
     "Compare ticket configurations in price order, including discounts, luggage, flexibility and meals.",
     ("Projection", "Column alias", "ORDER BY")),
    ("Revenue generated per flight",
     "Rank flights that have confirmed bookings by total confirmed payments.",
     ("GROUP BY", "COUNT", "SUM")),
    ("Airport geographical information",
     "Locate each airport within its city and country using the normalized geographic relations.",
     ("Multiple joins", "Foreign keys", "ORDER BY")),
    ("Confirmed passengers per flight",
     "Count confirmed booking records for every scheduled flight, including flights with zero confirmations.",
     ("LEFT JOIN", "COUNT", "GROUP BY")),
    ("Administrator-wise flight management",
     "Show which administrator manages each scheduled flight and its departure and arrival times.",
     ("INNER JOIN", "CONCAT", "ORDER BY")),
    ("Passenger contact information",
     "List every passenger and each registered phone number, including passengers without a phone.",
     ("LEFT JOIN", "One-to-many relationship", "NULL")),
    ("Available seats per flight",
     "Subtract confirmed bookings from model capacity to show seats without a confirmed booking. The unique seat constraint also reserves seat numbers on pending and cancelled records.",
     ("LEFT JOIN", "COUNT", "Calculated column")),
    ("Passengers with multiple confirmed bookings",
     "Identify repeat passengers by retaining groups with more than one confirmed booking.",
     ("GROUP BY", "HAVING", "COUNT")),
    ("Above-average booking payments",
     "Find confirmed payments that exceed the average payment across all confirmed bookings.",
     ("Scalar subquery", "AVG", "WHERE")),
    ("Flight occupancy percentage",
     "Express confirmed bookings as a percentage of aircraft capacity for each scheduled flight.",
     ("LEFT JOIN", "GROUP BY", "ROUND")),
    ("Airline-wise revenue",
     "Compare confirmed revenue and bookings across airlines with scheduled flights, and count each flight once.",
     ("COUNT DISTINCT", "SUM", "COALESCE")),
    ("Confirmed bookings view",
     "Read the reusable view that combines passenger, flight, seat, ticket class and payment for confirmed bookings.",
     ("VIEW", "INNER JOIN", "WHERE")),
)


def _load_catalog():
    # Project.sql is a trusted application file. Only these fixed SELECTs are
    # eligible for execution. USE, SHOW and the view definition are excluded.
    source = Path(__file__).with_name("Project.sql").read_text(encoding="utf-8-sig")
    statements = [part.strip() for part in source.split(";") if part.strip()]
    selects = [sql for sql in statements if sql.split(maxsplit=1)[0].upper() == "SELECT"]
    views = [sql for sql in statements
             if sql.upper().startswith("CREATE OR REPLACE VIEW CONFIRMED_BOOKINGS AS")]
    if len(selects) != len(CATALOG) or len(views) != 1:
        raise ValueError("Project.sql must contain the supplied 17 demonstrations and view definition.")
    demos = {}
    for number, (metadata, sql) in enumerate(zip(CATALOG, selects), start=1):
        title, requirement, concepts = metadata
        demos[number] = Demonstration(number, title, requirement, concepts, sql)
    return demos, views[0]


DEMOS, VIEW_DEFINITION = _load_catalog()


# The template escapes token text just as it does any other displayed value.
TOKEN_PATTERN = re.compile(
    r"(?P<string>'(?:''|[^'])*')|"
    r"(?P<keyword>\b(?:SELECT|FROM|AS|JOIN|ON|WHERE|AND|LEFT|GROUP|BY|ORDER|DESC|"
    r"HAVING|DISTINCT|CREATE|OR|REPLACE|VIEW)\b)|"
    r"(?P<function>\b(?:AVG|CONCAT|COUNT|SUM|ROUND|COALESCE)\b)|"
    r"(?P<number>\b\d+(?:\.\d+)?\b)", re.IGNORECASE
)


def sql_tokens(source):
    """Split SQL for lightweight highlighting while preserving its exact text."""
    end = 0
    for token in TOKEN_PATTERN.finditer(source):
        if token.start() > end:
            yield "", source[end:token.start()]
        yield token.lastgroup, token.group()
        end = token.end()
    if end < len(source):
        yield "", source[end:]
