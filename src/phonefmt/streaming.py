"""Streaming helpers for normalizing large batches of phone numbers.

The point of this module: nothing here calls `.read()` or `.readlines()`
on the whole input, and nothing collects results into a list before
handing them back. Every function consumes and produces one line at a
time, so a caller can point `normalize_stream` at a multi-gigabyte file
(or an open socket, or a subprocess pipe) and it runs in roughly constant
memory regardless of input size.
"""

from __future__ import annotations

from typing import IO, Iterable, Iterator, NamedTuple, Optional

from .core import ParsedNumber, PhoneNumberError, parse


class NormalizeResult(NamedTuple):
    line_number: int
    raw: str
    parsed: Optional[ParsedNumber]
    error: Optional[str]


def iter_normalize(
    lines: Iterable[str],
    default_region: Optional[str] = None,
) -> Iterator[NormalizeResult]:
    """Parse each line as a phone number, yielding one result per line.

    `lines` can be a file object, a list, or any other iterable that
    produces one entry at a time -- it is consumed lazily and never
    materialized in full. Blank lines are skipped.
    """
    for line_number, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed = parse(raw, default_region=default_region)
        except PhoneNumberError as exc:
            yield NormalizeResult(line_number, raw, None, str(exc))
        else:
            yield NormalizeResult(line_number, raw, parsed, None)


def normalize_stream(
    input_stream: IO[str],
    output_stream: IO[str],
    style: str = "e164",
    default_region: Optional[str] = None,
    errors_stream: Optional[IO[str]] = None,
) -> None:
    """Read phone numbers from `input_stream`, one per line, and write
    formatted numbers to `output_stream`, one per line.

    Both streams are handled incrementally, so this can sit between two
    open files or pipe ends without ever buffering the whole input.
    Lines that fail to parse are written to `errors_stream` as
    `line_number\\traw\\treason` if given, otherwise silently dropped.
    """
    for result in iter_normalize(input_stream, default_region=default_region):
        if result.parsed is None:
            if errors_stream is not None:
                errors_stream.write(f"{result.line_number}\t{result.raw}\t{result.error}\n")
            continue
        output_stream.write(result.parsed.format(style))
        output_stream.write("\n")
