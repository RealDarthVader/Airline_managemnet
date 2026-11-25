"""Small MySQL helpers. Every request owns and closes its connections."""

import os
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from dotenv import dotenv_values

ENV_FILE = Path(__file__).with_name(".env")


def settings():
    """Read local changes on the next request. Explicit process settings win."""
    local = dotenv_values(ENV_FILE)
    defaults = {"DB_HOST": "localhost", "DB_PORT": "3306", "DB_USER": "root",
                "DB_PASSWORD": "", "DB_NAME": "airline_management"}
    return {key: os.environ.get(key, local.get(key, default)) for key, default in defaults.items()}


def connect():
    config = settings()
    try:
        port = int(config["DB_PORT"])
        if not 1 <= port <= 65535:
            raise ValueError
    except (ValueError, TypeError):
        raise mysql.connector.InterfaceError(msg="Invalid DB_PORT setting", errno=2003) from None
    return mysql.connector.connect(
        host=config["DB_HOST"],
        port=port,
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        connection_timeout=5,
        charset="utf8mb4",
        autocommit=False,
    )


@contextmanager
def transaction():
    """One physical connection and one transaction, including all row locks."""
    connection = connect()
    try:
        with connection.cursor(dictionary=True, buffered=True) as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_all(sql, params=()):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def fetch_one(sql, params=()):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()
