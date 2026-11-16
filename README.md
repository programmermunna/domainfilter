# domainfilter

Find available domains fast. Paste comma-separated names, instantly see which
domains are **available** and their **estimated prices**, and get the filtered
results saved to separate files.

Built by **[programmermunna](https://github.com/programmermunna)** · MIT License · Zero dependencies

## Features

- **Comma-based input** — just paste `domain_name, srijon, uddog` and go
- **Real availability** via RDAP (the official successor to WHOIS) — free, no API key
- **Price estimates** for ~85 TLDs shown next to every available domain
- **Filtered output files** — available domains go in `available.txt`, taken in `taken.txt`, full data in `report.csv` / `report.json`
- **Parallel checks** — hundreds of domains in seconds
- **Pure Python stdlib** — nothing to install beyond Python 3.9+

## Install

```bash
git clone https://github.com/programmermunna/domainfilter.git
cd domainfilter
pip install .
```

Or run without installing:

```bash
python -m domainfilter "domain_name, srijon, uddog"
```

## Usage

```bash
# The simplest case — comma-separated names
domainfilter "domain_name, srijon, uddog, prava, nirmaan, disha, goti, oikko, setu"

# Pick your own TLDs
domainfilter "domain_name, srijon" --tlds com,ai,io,dev

# Check exact domains (dots mean "check this one only")
domainfilter "domain_name.com, srijon.ai"

# Read names from a file, or pipe them in
domainfilter --input input/names.txt
cat names.txt | domainfilter

# Multiple files at once — files, a folder, or a glob
domainfilter -i input/a.txt input/b.txt
domainfilter -i input/            # every .txt in the folder
domainfilter -i "input/*.txt"     # same, via glob

# Direct from files and tlds
domainfilter -i input/names.txt --tlds com,ai,dev

# Only print the available ones / machine-readable output
domainfilter "domain_name" --quiet
domainfilter "domain_name" --json

# Put results somewhere else, or skip saving entirely
domainfilter "domain_name" --out-dir results/run1
domainfilter "domain_name" --no-save
```

Example output:

```
domainfilter 1.0.0 — checking 144 domains across 16 TLDs...

  domain_name.com     taken       -
  domain_name.ai      available   $68.99/yr
  domain_name.dev     available   $12.99/yr
  srijon.com    taken       -
  ...

41 available, 99 taken, 4 unknown (144 checked)
saved → output/available.txt, output/taken.txt, output/unknown.txt, output/report.csv, output/report.json
* prices are estimates — confirm at your registrar before buying
```

## Output files

| File | Contents |
|------|----------|
| `output/available.txt` | Available domains with estimated price — ready to copy into a registrar's bulk search |
| `output/taken.txt` | Registered domains |
| `output/unknown.txt` | Couldn't be checked (only written if any exist) |
| `output/report.csv` | Everything, spreadsheet-friendly |
| `output/report.json` | Everything, machine-friendly |

Files go in a directory named after your input: `-i names.txt` produces
`output/names/available.txt`, `output/names/taken.txt`, etc. A folder input
uses the folder name (`output/input/` for `-i input/`), and multiple files
or a glob land in `output/combined/`. Re-filtering the same input clears
its old output first — stale data from previous runs never lingers.

## Options

```
names                  comma-separated names or domains
-i, --input FILE(S)    read names from file(s), a folder, or a glob
-t, --tlds LIST        TLDs to try (default: 16 popular ones)
-o, --out-dir DIR      output folder (default: output/)
--no-save              don't write result files
--json                 print results as JSON
-q, --quiet            only show available domains
-w, --workers N        parallel checks (default: 8)
--timeout SECS         per-request timeout (default: 10)
--no-color             disable colored output
```

## How it works

Availability is checked with **RDAP** — the IETF-standard protocol that
replaced WHOIS. The tool loads IANA's bootstrap registry to find each TLD's
RDAP server, then queries it directly: HTTP `404` means available, `200`
means taken. No API key, no scraping, no rate-limited third-party service.

Prices come from a built-in table of typical first-year USD registration
prices (`domainfilter/prices.py`). They're estimates — registrars run
promotions, charge different renewals, and some names are premium-priced.
Always confirm at checkout.

A result of `unknown` means the TLD's registry couldn't be reached or
doesn't publish RDAP — not that the domain is available.

## Development

```bash
python -m unittest discover -s tests   # run the test suite
```

Project layout:

```
domainfilter/     the package (cli, parser, checker, prices, report)
tests/            unittest suite (no network needed — RDAP is stubbed)
examples/         sample input file
```

## Contributing

Issues and PRs welcome at
[github.com/programmermunna/domainfilter](https://github.com/programmermunna/domainfilter).

## License

MIT — see [LICENSE.md](LICENSE.md).
