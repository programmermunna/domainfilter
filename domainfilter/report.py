"""Write filtered results to separate output files."""

import csv
import json
from pathlib import Path

from .checker import Status
from .prices import format_price


def _line(result):
    return f"{result.domain}\t{format_price(result.price)}"


def _output_paths(out_dir, stem):
    target = out_dir / stem if stem else out_dir
    target.mkdir(parents=True, exist_ok=True)
    return {
        "available": target / "available.txt",
        "taken": target / "taken.txt",
        "unknown": target / "unknown.txt",
        "report_csv": target / "report.csv",
        "report_json": target / "report.json",
    }


def write_reports(results, out_dir, stem=None):
    """Write available.txt, taken.txt, unknown.txt, report.csv, report.json.

    `stem` puts them in a named subdirectory (e.g. 'names' ->
    out_dir/names/available.txt). Files from a previous run in the same
    directory are removed first, so a re-filter never leaves stale data.

    Returns a dict of what was written: {'available': Path, 'taken': Path,
    'unknown': Path|None, 'report_csv': Path, 'report_json': Path}.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = _output_paths(out_dir, stem)
    for path in paths.values():
        path.unlink(missing_ok=True)

    by_status = {
        Status.AVAILABLE: [r for r in results if r.status == Status.AVAILABLE],
        Status.TAKEN: [r for r in results if r.status == Status.TAKEN],
        Status.UNKNOWN: [r for r in results if r.status == Status.UNKNOWN],
    }

    available_path = paths["available"]
    available_path.write_text(
        "\n".join(_line(r) for r in by_status[Status.AVAILABLE]) + "\n"
        if by_status[Status.AVAILABLE]
        else ""
    )

    taken_path = paths["taken"]
    taken_path.write_text(
        "\n".join(r.domain for r in by_status[Status.TAKEN]) + "\n"
        if by_status[Status.TAKEN]
        else ""
    )

    if by_status[Status.UNKNOWN]:
        paths["unknown"].write_text(
            "\n".join(r.domain for r in by_status[Status.UNKNOWN]) + "\n"
        )
    else:
        paths["unknown"] = None

    csv_path = paths["report_csv"]
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["domain", "status", "price_usd_year"])
        for r in results:
            writer.writerow(
                [r.domain, r.status.value, f"{r.price:.2f}" if r.price is not None else ""]
            )
    json_path = paths["report_json"]
    json_path.write_text(
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
        + "\n"
    )

    return paths
