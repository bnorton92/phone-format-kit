# phonefmt

A small Python library for parsing, validating, and reformatting phone
numbers. No third-party dependencies -- standard library only.

## Why

Most phone number input is inconsistent: `(415) 555-0100`, `415.555.0100`,
`+1 415 555 0100`, `1-415-555-0100` might all refer to the same number,
and you usually want to store or compare them in one canonical form
(E.164, typically). `phonefmt` parses the common formats, validates the
digit count against a small table of national numbering plans, and
formats the result however you need it.

It also has to work on things bigger than a Python list can comfortably
hold -- a log file, a CSV export, a stream of numbers coming off a queue.
`phonefmt.streaming` processes one line at a time and never buffers the
whole input, so normalizing a ten-million-line file uses about the same
memory as normalizing ten lines.

## Install

Not published anywhere yet. Clone it and install in editable mode:

```
pip install -e .
```

## Usage

```python
from phonefmt import parse, is_valid

parsed = parse("+1 (415) 555-0100")
parsed.e164()           # "+14155550100"
parsed.international()  # "+1 4155550100"

parsed = parse("(415) 555-0100", default_region="US")
parsed.e164()            # "+14155550100"

is_valid("+1 555 0100")  # False -- wrong number of digits for NANP
```

### Streaming a large file

```python
from phonefmt import normalize_stream

with open("raw_numbers.txt") as src, open("normalized.txt", "w") as dst, \
     open("errors.tsv", "w") as errs:
    normalize_stream(src, dst, style="e164", default_region="US", errors_stream=errs)
```

`normalize_stream` reads `raw_numbers.txt` and writes `normalized.txt` one
line at a time; it never calls `read()` or `readlines()`, so the input
file's size has no bearing on memory use. Lines that don't parse are
logged to `errors.tsv` with the line number and the reason, instead of
aborting the whole run.

If you want to inspect results instead of just writing formatted text,
`iter_normalize` yields a `NormalizeResult(line_number, raw, parsed, error)`
per line and is just as lazy:

```python
from phonefmt import iter_normalize

with open("raw_numbers.txt") as src:
    for result in iter_normalize(src, default_region="US"):
        if result.error:
            print(f"line {result.line_number}: {result.error}")
        else:
            print(result.parsed.e164())
```

## Supported regions

US, CA, GB, DE, FR, AU, IN, JP, BR, MX, NL, ES -- see `phonefmt.core.PLANS`. This is a
hand-picked list, not a full numbering plan database; adding a region
means adding an entry to `PLANS` plus a test fixture that shows a real
example number.

## Running tests

```
python -m unittest discover -s tests
```

## License

MIT, see LICENSE.
