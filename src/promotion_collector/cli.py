from __future__ import annotations

import argparse
import sys

from promotion_collector.collector import Collector
from promotion_collector.config import list_city_configs, load_city_config
from promotion_collector.http_client import HttpClient
from promotion_collector.sources import OverpassSource, SeedSiteSource, Source


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-"):
        argv = ["collect", *argv]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-cities":
        for slug in list_city_configs():
            print(slug)
        return 0

    config = load_city_config(args.city)
    http = HttpClient(delay_seconds=args.delay)
    sources = build_sources(args.sources, http, enrich_websites=not args.no_enrich_websites)
    result = Collector(sources).collect(config, args.limit)
    http.close()

    print(f"City: {config.name}")
    print(f"Scanned candidate records: {result.scanned}")
    print(f"New unique records: {result.unique}")
    print(f"JSON: {result.json_path}")
    print(f"XLSX: {result.xlsx_path}")
    if result.sheet_name:
        print(f"New sheet: {result.sheet_name}")
    else:
        print("No XLSX sheet added because there were no new unique records.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promotion-collector",
        description="Collect public business contacts by city into JSON and XLSX files.",
    )
    subparsers = parser.add_subparsers(dest="command")

    collect = subparsers.add_parser("collect", help="collect contacts for a city")
    collect.add_argument("--city", default="nha-trang", help="city config slug")
    collect.add_argument("--limit", type=int, default=10, help="max unique records to add")
    collect.add_argument(
        "--sources",
        nargs="+",
        default=["overpass", "seed"],
        choices=["overpass", "seed"],
        help="sources to use",
    )
    collect.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="polite delay between requests to the same domain",
    )
    collect.add_argument(
        "--no-enrich-websites",
        action="store_true",
        help="skip website visits for map results",
    )

    subparsers.add_parser("list-cities", help="show available city configs")
    return parser


def build_sources(names: list[str], http: HttpClient, enrich_websites: bool) -> list[Source]:
    sources: list[Source] = []
    if "overpass" in names:
        sources.append(OverpassSource(http=http, enrich_websites=enrich_websites))
    if "seed" in names:
        sources.append(SeedSiteSource(http=http))
    return sources


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
