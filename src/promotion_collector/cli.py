from __future__ import annotations

import argparse
import sys

from promotion_collector.collector import Collector
from promotion_collector.config import (
    get_city_group,
    list_city_configs,
    list_city_groups,
    load_city_config,
)
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

    if args.command == "list-groups":
        for group in list_city_groups():
            print(group)
        return 0

    http = HttpClient(delay_seconds=args.delay)
    sources = build_sources(args.sources, http, enrich_websites=not args.no_enrich_websites)
    collector = Collector(sources)

    if args.command == "collect-group":
        for city_slug in get_city_group(args.group):
            config = load_city_config(city_slug)
            result = collector.collect(config, args.limit)
            print_collection_result(config.name, result)
        http.close()
        return 0

    config = load_city_config(args.city)
    result = collector.collect(config, args.limit)
    http.close()

    print_collection_result(config.name, result)
    return 0


def print_collection_result(city_name: str, result) -> None:
    print(f"City: {city_name}")
    print(f"Scanned candidate records: {result.scanned}")
    print(f"New unique records: {result.unique}")
    print(f"JSON: {result.json_path}")
    print(f"XLSX: {result.xlsx_path}")
    if result.sheet_name:
        print(f"New sheet: {result.sheet_name}")
    else:
        print("No XLSX sheet added because there were no new unique records.")
    print("")


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

    group = subparsers.add_parser("collect-group", help="collect contacts for a city group")
    group.add_argument("--group", default="russia-million-plus", help="city group name")
    group.add_argument("--limit", type=int, default=10, help="max unique records to add per city")
    group.add_argument(
        "--sources",
        nargs="+",
        default=["overpass", "seed"],
        choices=["overpass", "seed"],
        help="sources to use",
    )
    group.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="polite delay between requests to the same domain",
    )
    group.add_argument(
        "--no-enrich-websites",
        action="store_true",
        help="skip website visits for map results",
    )

    subparsers.add_parser("list-cities", help="show available city configs")
    subparsers.add_parser("list-groups", help="show available city groups")
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
