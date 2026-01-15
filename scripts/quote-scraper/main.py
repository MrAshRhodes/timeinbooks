#!/usr/bin/env python3
"""Quote scraper CLI - Find and extract time-related quotes."""
import argparse
import json
import sys
from typing import Dict, List

from sources import GutenbergSource, ScriptSource
from formatter import Quote
from merger import run_merge, save_new_quotes
from deduper import dedupe_by_time


def scrape_gutenberg(max_books: int = 15) -> Dict[str, List[Quote]]:
    """Scrape quotes from Project Gutenberg."""
    source = GutenbergSource(max_books=max_books)
    return source.scrape()


def scrape_scripts(max_scripts: int = 10) -> Dict[str, List[Quote]]:
    """Scrape quotes from movie scripts."""
    source = ScriptSource(max_scripts=max_scripts)
    return source.scrape()


def merge_results(*results: Dict[str, List]) -> Dict[str, List]:
    """Merge multiple scrape results."""
    merged = {}
    for result in results:
        for time_key, quotes in result.items():
            if time_key not in merged:
                merged[time_key] = []
            merged[time_key].extend(quotes)
    return dedupe_by_time(merged)


def print_stats(quotes: Dict[str, List]):
    """Print statistics about scraped quotes."""
    total = sum(len(v) for v in quotes.values())
    times_covered = len(quotes)

    print(f"\n{'='*50}")
    print(f"Scrape Results:")
    print(f"  Total quotes: {total}")
    print(f"  Times covered: {times_covered}/1440 ({times_covered/1440*100:.1f}%)")

    # Show distribution by hour
    by_hour = {}
    for time_key in quotes:
        hour = int(time_key.split(':')[0])
        by_hour[hour] = by_hour.get(hour, 0) + len(quotes[time_key])

    print(f"\n  Quotes by hour:")
    for hour in sorted(by_hour.keys()):
        bar = '█' * (by_hour[hour] // 5)
        print(f"    {hour:02d}:00 - {by_hour[hour]:3d} {bar}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape quotes containing time references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --source gutenberg --max 5
  python main.py --source scripts --max 10
  python main.py --source all --merge
  python main.py --source gutenberg --dry-run
        """
    )

    parser.add_argument(
        '--source',
        choices=['gutenberg', 'scripts', 'all'],
        default='all',
        help='Quote source to scrape'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=10,
        help='Maximum items to scrape per source'
    )
    parser.add_argument(
        '--merge',
        action='store_true',
        help='Merge results into quotes.js'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Save to new_quotes.json instead of merging'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file for scraped quotes'
    )

    args = parser.parse_args()

    all_quotes = {}

    # Run scrapers
    if args.source in ['gutenberg', 'all']:
        print("\n[Gutenberg] Starting...")
        gutenberg_quotes = scrape_gutenberg(max_books=args.max)
        all_quotes = merge_results(all_quotes, gutenberg_quotes)

    if args.source in ['scripts', 'all']:
        print("\n[Scripts] Starting...")
        script_quotes = scrape_scripts(max_scripts=args.max)
        all_quotes = merge_results(all_quotes, script_quotes)

    # Print stats
    print_stats(all_quotes)

    # Handle output
    if args.output:
        # Save to specified JSON file
        output_dict = {
            time_key: [q.to_dict() if isinstance(q, Quote) else q for q in quotes]
            for time_key, quotes in all_quotes.items()
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_dict, f, indent=2)
        print(f"\nSaved to {args.output}")

    elif args.merge or args.dry_run:
        # Merge into quotes.js
        run_merge(all_quotes, dry_run=args.dry_run)

    else:
        # Just save for review
        path = save_new_quotes(all_quotes)
        print(f"\nSaved to {path}")
        print("Use --merge to add to quotes.js, or --dry-run to preview")


if __name__ == '__main__':
    main()
