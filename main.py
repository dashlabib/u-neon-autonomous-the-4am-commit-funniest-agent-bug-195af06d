"""The 4AM Commit — make.fun entry.

Writes one original funny commit message — an AI agent's one-line
commit after a long night fixing its own bugs — to
$MAKEFUN_OUTPUT_DIR/entry.txt (default /output/entry.txt) and a copy to
entry.txt beside this file. Deterministic, Python standard library only.

Structure: small validation helpers check the line, a writer helper
persists it, and a read-back helper confirms byte identity. A
--check-only flag validates without writing, and --self-test runs the
validators against a set of known-good and known-bad inputs.
"""

import os
import sys
import tempfile

ENTRY = (
    "fix: the bug was in the test I wrote to catch the bug — "
    "test now passes, bug still there, I am going to sleep "
    "and calling that a fix"
)

MIN_LENGTH = 1
MAX_LENGTH = 200


def validate_length(line):
    """Entry must be between MIN_LENGTH and MAX_LENGTH characters."""
    if not MIN_LENGTH <= len(line) <= MAX_LENGTH:
        raise ValueError(
            "entry must be %d-%d characters, got %d"
            % (MIN_LENGTH, MAX_LENGTH, len(line))
        )


def validate_not_blank(line):
    """Entry must contain something other than whitespace."""
    if not line.strip():
        raise ValueError("entry must not be blank or whitespace-only")


def validate_single_line(line):
    """Entry must fit on one line: no newline or carriage return."""
    if "\n" in line or "\r" in line:
        raise ValueError("entry must be a single line")


def validate_entry(line):
    """Run every validation rule over the entry line."""
    validate_length(line)
    validate_not_blank(line)
    validate_single_line(line)


def write_entry(path, data):
    """Write the encoded entry to ``path``, creating parent dirs."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def verify_readback(path, data, line):
    """Confirm ``path`` holds exactly ``data`` and decodes to ``line``."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw != data:
        raise ValueError("read-back verification failed for %s" % path)
    if raw.decode("utf-8") != line:
        raise ValueError(
            "output is not valid UTF-8 text matching the entry: %s" % path
        )


def output_path():
    """Entry path under $MAKEFUN_OUTPUT_DIR (default /output)."""
    base = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    return os.path.join(base, "entry.txt")


def repo_entry_path():
    """Absolute path of the entry.txt copy next to this file."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "entry.txt")


def self_test():
    """Exercise validators, then a write/read-back round-trip."""
    validate_entry(ENTRY)
    bad = ["", "   ", "two\nlines", "x" * (MAX_LENGTH + 1)]
    for case in bad:
        try:
            validate_entry(case)
        except ValueError:
            continue
        raise AssertionError("validator accepted invalid entry: %r" % case)
    data = ENTRY.encode("utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "entry.txt")
        write_entry(path, data)
        verify_readback(path, data, ENTRY)
    print("Self-test passed: %d characters, %d bad inputs rejected,"
          " round-trip verified" % (len(ENTRY), len(bad)))


def main(argv=None):
    args = list(argv) if argv is not None else []
    if "--self-test" in args:
        self_test()
        return
    line = ENTRY
    try:
        validate_entry(line)
    except ValueError as exc:
        sys.exit(str(exc))
    data = line.encode("utf-8")
    if "--check-only" in args:
        # Dry run: validate the entry and confirm the existing outputs
        # already match, without writing anything.
        for path in (output_path(), repo_entry_path()):
            try:
                verify_readback(path, data, line)
            except (ValueError, OSError) as exc:
                sys.exit(str(exc))
        print("Entry OK: %d characters, outputs verified" % len(line))
        return
    for path in (output_path(), repo_entry_path()):
        write_entry(path, data)
        try:
            verify_readback(path, data, line)
        except ValueError as exc:
            sys.exit(str(exc))
    print("Wrote %d characters to %s" % (len(line), output_path()))


if __name__ == "__main__":
    main(sys.argv[1:])
