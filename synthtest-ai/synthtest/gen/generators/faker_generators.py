from __future__ import annotations

from synthtest.util.rng import Rng

FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Riley", "Jamie", "Casey", "Avery", "Quinn"]
LAST_NAMES = ["Smith", "Patel", "Kim", "Garcia", "Brown", "Jones", "Miller", "Davis", "Wilson", "Clark"]
DOMAINS = ["example.com", "test.local", "sample.org", "demo.dev"]
COUNTRIES = ["United Kingdom", "United States", "Canada", "Germany", "France", "Australia", "Japan", "Brazil"]
PHONE_PREFIXES = ["+1", "+44", "+49", "+33", "+81", "+61"]
UK_AREAS = ["SW", "SE", "NW", "NE", "EC", "WC", "W", "E", "N", "S", "B", "M", "L", "G", "EH"]


def generate_name(rng: Rng) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def generate_email(rng: Rng) -> str:
    local = f"{rng.choice(FIRST_NAMES)}.{rng.choice(LAST_NAMES)}".lower()
    return f"{local}@{rng.choice(DOMAINS)}"


def generate_phone(rng: Rng) -> str:
    prefix = rng.choice(PHONE_PREFIXES)
    number = "".join(str(rng.randint(0, 9)) for _ in range(10))
    return f"{prefix}{number}"


def generate_country(rng: Rng) -> str:
    return rng.choice(COUNTRIES)


def generate_postcode_uk(rng: Rng) -> str:
    area = rng.choice(UK_AREAS)
    district = f"{rng.randint(1, 9)}"
    sector = f"{rng.randint(0, 9)}"
    unit = f"{chr(rng.randint(65, 90))}{chr(rng.randint(65, 90))}"
    return f"{area}{district} {sector}{unit}"
