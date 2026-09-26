"""Parsing and formatting for phone numbers.

This covers a small, hand-picked set of national numbering plans rather
than trying to be a complete implementation of the ITU-T E.164 numbering
scheme. It's enough to validate and reformat numbers from the regions
listed in PLANS; it is not a replacement for a full numbering plan
database like the one libphonenumber ships with.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NON_DIGITS = re.compile(r"[^\d+]")


class PhoneNumberError(ValueError):
    """Raised when a string cannot be parsed as a phone number."""


@dataclass(frozen=True)
class NumberPlan:
    region: str
    country_code: str
    national_lengths: tuple[int, ...]
    trunk_prefix: str = ""


# Deliberately small. Adding a region means adding a plan here and a
# fixture in the test suite -- most numbering plans have quirks (variable
# length national numbers, area codes with their own rules) that are easy
# to get wrong without a real example to check against.
PLANS: dict[str, NumberPlan] = {
    "US": NumberPlan("US", "1", (10,), trunk_prefix="1"),
    "CA": NumberPlan("CA", "1", (10,), trunk_prefix="1"),
    "GB": NumberPlan("GB", "44", (10,), trunk_prefix="0"),
    "DE": NumberPlan("DE", "49", (10, 11), trunk_prefix="0"),
    "FR": NumberPlan("FR", "33", (9,), trunk_prefix="0"),
    "AU": NumberPlan("AU", "61", (9,), trunk_prefix="0"),
    "IN": NumberPlan("IN", "91", (10,), trunk_prefix="0"),
    # 9 digits for fixed lines under a 2-digit area code (e.g. Tokyo's 03),
    # 10 for mobile numbers (which carry a 3-digit 0[789]0 prefix).
    "JP": NumberPlan("JP", "81", (9, 10), trunk_prefix="0"),
    # 10 for fixed lines (2-digit area code + 8-digit number), 11 for
    # mobile (2-digit area code + 9-digit number, the extra digit being
    # the mandatory leading "9" mobiles have carried since 2012-2016).
    "BR": NumberPlan("BR", "55", (10, 11), trunk_prefix="0"),
    # Since the 2019 renumbering, all national numbers are dialed as a
    # flat 10 digits (2-3 digit area code + subscriber number) with no
    # trunk prefix and no "1" before mobile numbers.
    "MX": NumberPlan("MX", "52", (10,)),
    "NL": NumberPlan("NL", "31", (9,), trunk_prefix="0"),
    # Spain never adopted a trunk prefix -- even local calls dial the
    # full 9-digit number.
    "ES": NumberPlan("ES", "34", (9,)),
}

# Longest country code first, so "+1" doesn't shadow a hypothetical
# two-digit code that happens to start with the same digit.
_BY_COUNTRY_CODE = sorted(
    ((plan.country_code, plan) for plan in PLANS.values()),
    key=lambda pair: -len(pair[0]),
)


@dataclass(frozen=True)
class ParsedNumber:
    region: str
    country_code: str
    national_number: str

    def e164(self) -> str:
        return f"+{self.country_code}{self.national_number}"

    def international(self) -> str:
        return f"+{self.country_code} {self.national_number}"

    def national(self) -> str:
        plan = PLANS[self.region]
        return f"{plan.trunk_prefix}{self.national_number}"

    def format(self, style: str = "e164") -> str:
        method = getattr(self, style, None)
        if method is None or not callable(method):
            raise ValueError(f"unknown format style: {style!r}")
        return method()


def parse(raw: str, default_region: str | None = None) -> ParsedNumber:
    """Parse a free-form phone number string.

    `raw` may contain spaces, dashes, parentheses, dots, and a leading
    `+`. If it doesn't start with `+`, `default_region` is used to supply
    the country code and to know which trunk prefix to strip.
    """
    digits = _NON_DIGITS.sub("", raw)
    if not digits:
        raise PhoneNumberError(f"no digits found in {raw!r}")

    if digits.startswith("+"):
        digits = digits[1:]
        for country_code, plan in _BY_COUNTRY_CODE:
            if digits.startswith(country_code):
                national = digits[len(country_code):]
                return _validate(plan, national, raw)
        raise PhoneNumberError(f"unrecognized country code in {raw!r}")

    if default_region is None:
        raise PhoneNumberError(
            f"{raw!r} has no country code and no default_region was given"
        )
    plan = PLANS.get(default_region)
    if plan is None:
        raise PhoneNumberError(f"unknown region: {default_region!r}")

    national = digits
    if plan.trunk_prefix and national.startswith(plan.trunk_prefix):
        national = national[len(plan.trunk_prefix):]
    return _validate(plan, national, raw)


def _validate(plan: NumberPlan, national: str, raw: str) -> ParsedNumber:
    if len(national) not in plan.national_lengths:
        raise PhoneNumberError(
            f"{raw!r} has {len(national)} national digits, expected one "
            f"of {plan.national_lengths} for {plan.region}"
        )
    return ParsedNumber(
        region=plan.region, country_code=plan.country_code, national_number=national
    )


def is_valid(raw: str, default_region: str | None = None) -> bool:
    try:
        parse(raw, default_region=default_region)
    except PhoneNumberError:
        return False
    return True
