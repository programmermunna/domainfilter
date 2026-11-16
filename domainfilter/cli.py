"""Command-line interface for domainfilter."""

import argparse
import glob
import json
import sys
from pathlib import Path

from . import __version__
from .checker import Status, iter_checked_domains
from .parser import expand_domains, parse_names, parse_tlds
from .prices import format_price
from .report import write_reports

DEFAULT_TLDS = [
    "com", "net", "org", "io", "ai", "dev", "app", "co",
    "xyz", "me", "tech", "shop", "online", "site", "store", "info",
]

_GREEN = "\033[32m"
_RED = "\033[31m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def build_parser():
    p = argparse.ArgumentParser(
        prog="domainfilter",
        description="Find available domains fast. Paste comma-separated names, "
        "see availability + estimated prices, save filtered results.",
        epilog="example: domainfilter \"kormo, srijon, uddog\" --tlds com,ai,io",
    )
    p.add_argument("names", nargs="?", help="comma-separated names or domains")
    p.add_argument(
        "-i", "--input", metavar="FILE", nargs="+",
        help="read names from file(s) — files, a folder of .txt files, "
        "or a glob like 'input/*.txt'",
    )
    p.add_argument(
        "-t", "--tlds", metavar="LIST",
        help=f"comma-separated TLDs (default: {','.join(DEFAULT_TLDS)})",
    )
    p.add_argument(
        "-o", "--out-dir", metavar="DIR", default="output",
        help="folder for result files (default: output/)",
    )
    p.add_argument("--no-save", action="store_true", help="don't write result files")
    p.add_argument("--json", action="store_true", help="print results as JSON")
    p.add_argument("-q", "--quiet", action="store_true", help="only show available domains")
    p.add_argument("-w", "--workers", type=int, default=8, help="parallel checks (default: 8)")
    p.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds")
    p.add_argument("--no-color", action="store_true", help="disable colored output")
    p.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _resolve_inputs(entries):
    """Turn -i entries (files, folders, glob patterns) into a path list."""
    paths = []
    for entry in entries:
        p = Path(entry)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.txt")))
        elif glob.has_magic(entry):
            paths.extend(
                Path(m) for m in sorted(glob.glob(entry, recursive=True))
            )
        else:
            paths.append(p)
    return paths


def _read_input(args, parser):
    """Return (raw text, output stem) for the chosen input source."""
    if args.names and args.input:
        parser.error("give names on the command line OR --input, not both")
    if args.input:
        paths = _resolve_inputs(args.input)
        if not paths:
            parser.error(f"no files matched: {' '.join(args.input)}")
        texts = []
        for p in paths:
            try:
                texts.append(p.read_text())
            except OSError as e:
                parser.error(f"can't read {p}: {e}")
        if len(paths) == 1:
            stem = paths[0].stem
        elif len(args.input) == 1 and Path(args.input[0]).is_dir():
            stem = Path(args.input[0]).name
        else:
            stem = "combined"
        return "\n".join(texts), stem
    if args.names:
        return args.names, None
    if not sys.stdin.isatty():
        return sys.stdin.read(), None
    parser.error("no input — pass comma-separated names, --input FILE(S), or pipe via stdin")


def _status_color(status, use_color):
    if not use_color:
        return ""
    return {Status.AVAILABLE: _GREEN, Status.TAKEN: _RED}.get(status, _DIM)


def _format_row(r, width, use_color):
    color = _status_color(r.status, use_color)
    label = r.status.value
    price = format_price(r.price) if r.status == Status.AVAILABLE else "-"
    row = f"  {r.domain.ljust(width)}  {label.ljust(9)}  {price}"
    return f"  {color}{row.lstrip()}{_RESET}" if use_color else row


def _print_json(results):
    print(
        json.dumps(
            [
                {
                    "domain": r.domain,
                    "status": r.status.value,
                    "price_usd_year": r.price,
                    "price_display": format_price(r.price),
                }
                for r in results
            ],
            indent=2,
        )
    )


def main(argv=None, *, fetch=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    text, stem = _read_input(args, parser)
    parsed = parse_names(text)

    for token in parsed.skipped:
        print(f"warning: skipped invalid name '{token}'", file=sys.stderr)
    if not parsed.tokens:
        print("error: no valid names found in input", file=sys.stderr)
        return 1

    tlds = parse_tlds(args.tlds) if args.tlds else list(DEFAULT_TLDS)
    domains = expand_domains(parsed.tokens, tlds)

    use_color = (
        sys.stdout.isatty() and not args.no_color and not args.json
    )
    if use_color:
        print(f"{_BOLD}domainfilter {__version__}{_RESET} — checking {len(domains)} domains across {len(tlds)} TLDs...\n")

    kwargs = dict(workers=args.workers, timeout=args.timeout)
    if fetch is not None:
        kwargs["fetch"] = fetch

    width = max(len(d) for d in domains)
    results = []
    for r in iter_checked_domains(domains, **kwargs):
        results.append(r)
        if not args.json and (not args.quiet or r.status == Status.AVAILABLE):
            print(_format_row(r, width, use_color), flush=True)

    if args.json:
        _print_json(results)

    counts = {s: sum(1 for r in results if r.status == s) for s in Status}
    print(
        f"\n{counts[Status.AVAILABLE]} available, "
        f"{counts[Status.TAKEN]} taken, "
        f"{counts[Status.UNKNOWN]} unknown "
        f"({len(results)} checked)"
    )

    if not args.no_save:
        paths = write_reports(results, args.out_dir, stem=stem)
        saved = ", ".join(f"{p}" for p in paths.values() if p)
        print(f"saved → {saved}")

    print("* prices are estimates — confirm at your registrar before buying")
    return 0
