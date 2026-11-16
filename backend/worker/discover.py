"""Discover new company job boards from the community GitHub job lists.

It downloads the public SimplifyJobs / Pitt CSC listing files, finds every
Greenhouse, Lever and Ashby job board they link to, tests each new board with
the pipeline's own collectors and CS/US/early-career filter, and (with --apply)
adds the working ones to the `companies` table.

Run from backend/worker with the virtual environment turned on:
    python discover.py                 # report only, from the GitHub lists (fast, no database)
    python discover.py --check 40      # also test 40 new boards (no database)
    python discover.py --apply         # test every new board, then add the working ones

--apply also saves each new company's current jobs once, without alerts, so
students aren't flooded with "new job" notifications for jobs that were posted
weeks ago. From then on, the regular pipeline collects these companies and
alerts only on genuinely new postings.
"""
import argparse
import collections
import concurrent.futures
import re
import time
from datetime import datetime, timezone

import requests

import pipeline

LISTS = {
    "Internships (Summer 2027)": "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json",
    "New grad": "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json",
}
SYSTEMS = ("greenhouse", "ashby", "lever")

# The board name is the first path segment after the job system's host.
BOARD_PATTERNS = {
    "greenhouse": re.compile(r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_app\?for=)?([A-Za-z0-9_-]+)"),
    "lever": re.compile(r"jobs\.lever\.co/([A-Za-z0-9_.-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
}
OTHER_SYSTEMS = {"myworkdayjobs": "Workday", "icims": "iCIMS", "smartrecruiters": "SmartRecruiters", "workable": "Workable"}
CHECK_WORKERS = 8


def job_system(url: str) -> tuple[str, str | None]:
    """Return (system, board name) for a job link; board name is None for other systems."""
    for system, pattern in BOARD_PATTERNS.items():
        match = pattern.search(url or "")
        if match:
            return system, match.group(1).lower()
    host = re.sub(r"^https?://(www\.)?", "", url or "").split("/")[0].lower()
    for key, name in OTHER_SYSTEMS.items():
        if key in host:
            return name, None
    return "Company's own site", None


def load_open_postings(url: str) -> list[dict]:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return [row for row in response.json() if row.get("active") and row.get("is_visible", True)]


def find_boards(postings: list[dict]) -> dict[tuple[str, str], str]:
    """(system, board) -> the company name the lists use most often for that board."""
    names: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for row in postings:
        system, board = job_system(row.get("url", ""))
        name = (row.get("company_name") or "").strip()
        if board and name:
            names[(system, board)][name] += 1
    return {key: counter.most_common(1)[0][0] for key, counter in names.items()}


def check_board(system: str, board: str, now: datetime) -> tuple[str, str, bool, int, list[dict]]:
    """Download one board with the pipeline's own collector and filters.
    Rows are built with company_id 0; assign the real id before saving."""
    try:
        raw = pipeline.collect(system, board)
        return system, board, True, len(raw), pipeline.clean_up(raw, 0, now, source=system)
    except Exception:  # a dead or renamed board: count it as not working
        return system, board, False, 0, []


def check_boards(boards: list[tuple[str, str]], now: datetime) -> list[tuple[str, str, bool, int, list[dict]]]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=CHECK_WORKERS) as pool:
        return list(pool.map(lambda item: check_board(*item, now), boards))


def with_company_id(rows: list[dict], company_id: int) -> list[dict]:
    """Rows from check_board, re-keyed for the company's real id (the fingerprint includes it)."""
    return [
        {**row, "company_id": company_id,
         "dedupe_hash": pipeline.make_fingerprint(company_id, row["title"], row["location"])}
        for row in rows
    ]


def existing_companies(supabase) -> list[dict]:
    rows, page_size, offset = [], 1000, 0
    while True:
        page = (supabase.table("companies").select("id, name, ats_type, ats_slug")
                .order("id").range(offset, offset + page_size - 1).execute().data)
        rows += page
        if len(page) < page_size:
            return rows
        offset += page_size


def plan_additions(results, names: dict[tuple[str, str], str], existing: list[dict], min_jobs: int):
    """Decide which checked boards to add. Returns (to_add, skipped) where to_add is a
    list of (name, system, board, rows) and skipped is a list of (name, reason)."""
    taken_boards = {(row.get("ats_type"), (row.get("ats_slug") or "").lower()) for row in existing}
    taken_names = {(row.get("name") or "").strip().lower() for row in existing}
    to_add, skipped = [], []
    for system, board, ok, _, rows in sorted(results, key=lambda r: -len(r[4])):
        name = names.get((system, board), board)
        if (system, board) in taken_boards:
            continue
        if not ok:
            skipped.append((name, f"{system} board '{board}' did not respond"))
        elif len(rows) < min_jobs:
            skipped.append((name, f"no current jobs pass our CS/US/early-career filter"))
        elif name.lower() in taken_names:
            skipped.append((name, "a company with this name is already in the table (check it by hand)"))
        else:
            to_add.append((name, system, board, rows))
            taken_names.add(name.lower())
            taken_boards.add((system, board))
    return to_add, skipped


def add_companies(supabase, to_add) -> tuple[int, int]:
    """Insert each company, then save its current jobs once with no notifications."""
    added = jobs_saved = 0
    for name, system, board, rows in to_add:
        try:
            inserted = supabase.table("companies").insert({"name": name, "ats_type": system, "ats_slug": board}).execute().data
            company_id = inserted[0]["id"]
            pipeline.save(supabase, with_company_id(rows, company_id), company_id)
        except Exception as error:  # one bad row shouldn't stop the rest
            print(f"    ! {name} ({system}/{board}): not added ({error})")
            continue
        added += 1
        jobs_saved += len(rows)
        print(f"    + {name} ({system}/{board}): {len(rows)} jobs")
    return added, jobs_saved


def show_board(system: str, board: str) -> None:
    """Print the titles one board keeps, most common first, to judge the filter by eye."""
    _, _, ok, raw, rows = check_board(system, board, datetime.now(timezone.utc))
    if not ok:
        print(f"{system} board '{board}' did not respond.")
        return
    titles = collections.Counter(row["title"] for row in rows)
    print(f"{system}/{board}: {len(rows)} jobs kept of {raw} ({len(titles)} different titles; "
          f"the same title in several cities counts once per city)\n")
    for title, count in titles.most_common():
        print(f"    {count:>3}  {title}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", type=int, default=0, metavar="N",
                        help="test N new boards with the real pipeline filters, without the database")
    parser.add_argument("--apply", action="store_true",
                        help="test every new board and add the working ones to the companies table")
    parser.add_argument("--min-jobs", type=int, default=1,
                        help="with --apply, only add boards with at least this many jobs passing our filter (default 1)")
    parser.add_argument("--yes", action="store_true", help="with --apply, skip the confirmation question")
    parser.add_argument("--show", metavar="SYSTEM/BOARD",
                        help="list the job titles one board keeps after our filter, e.g. greenhouse/spacex (no database)")
    args = parser.parse_args()

    if args.show:
        show_board(*args.show.lower().split("/", 1))
        return

    supabase = pipeline.get_client() if args.apply else None
    if supabase:
        existing = existing_companies(supabase)
        print(f"Career Hub collects from {len(existing)} companies today.\n")
    else:
        existing = [{"name": name, "ats_type": "greenhouse", "ats_slug": slug}
                    for name, slug in pipeline.STARTER_COMPANIES.items()]
        print(f"Career Hub's starter list has {len(existing)} companies (all on Greenhouse).\n")
    current = {(row.get("ats_type"), (row.get("ats_slug") or "").lower()) for row in existing}

    every_posting = []
    for list_name, url in LISTS.items():
        postings = load_open_postings(url)
        every_posting += postings
        systems = collections.Counter()
        for row in postings:
            system, board = job_system(row.get("url", ""))
            systems[system.capitalize() if board else system] += 1
        companies = {(row.get("company_name") or "").strip().lower() for row in postings}
        print(f"{list_name}: {len(postings):,} open postings from {len(companies):,} companies")
        for system, count in systems.most_common():
            print(f"    {system:<20} {count:>6,}")
        print()

    names = find_boards(every_posting)
    new_boards = sorted(key for key in names if key not in current)
    print(f"Job boards the lists link to that the pipeline can read: {len(names):,}")
    for system in SYSTEMS:
        found = sum(1 for key in names if key[0] == system)
        new = sum(1 for key in new_boards if key[0] == system)
        print(f"    {system:<10} {found:>4} boards, {new:>4} new to us")
    print(f"=> {len(existing)} companies today -> up to {len(existing) + len(new_boards):,} with GitHub discovery\n")

    if not (args.check or args.apply):
        print("Report only. No database changes were made.")
        return

    sample = new_boards
    if not args.apply:
        sample = new_boards[::max(1, len(new_boards) // args.check)][:args.check]  # spread across all systems
    print(f"Testing {len(sample)} new boards with the pipeline's collectors and CS/US/early-career filter...")
    started = time.time()
    results = check_boards(sample, datetime.now(timezone.utc))
    working = [r for r in results if r[2]]
    kept = sum(len(r[4]) for r in working)
    print(f"    {len(working)} of {len(results)} boards work, {sum(r[3] for r in working):,} jobs downloaded, "
          f"{kept:,} pass our filters ({time.time() - started:.0f}s)")
    if not working:
        print("    No board responded. Check the internet connection, then try again.")
    for system, board, _, raw, rows in sorted(working, key=lambda r: -len(r[4]))[:10]:
        print(f"    {names.get((system, board), board):<28} {system:<10} {len(rows):>4} CS jobs kept of {raw}")

    if not args.apply:
        if working:
            print(f"\n    Rough estimate across all {len(new_boards)} new boards: ~{kept / len(results) * len(new_boards):,.0f} more CS jobs")
        print("\nNo database changes were made.")
        return

    to_add, skipped = plan_additions(results, names, existing, args.min_jobs)
    print(f"\nReady to add {len(to_add)} companies with {sum(len(r[3]) for r in to_add):,} current CS jobs. "
          f"Skipping {len(skipped)}.")
    for name, reason in skipped[:15]:
        print(f"    - {name}: {reason}")
    if len(skipped) > 15:
        print(f"    ... and {len(skipped) - 15} more")
    if not to_add:
        return
    if not args.yes and input("\nAdd them to the database now? [y/N] ").strip().lower() != "y":
        print("Cancelled. No database changes were made.")
        return

    added, jobs_saved = add_companies(supabase, to_add)
    logos = pipeline.backfill_company_logos(supabase)
    print(f"\nDone. Added {added} companies and {jobs_saved:,} jobs (no alerts sent), {logos} logos guessed.")
    print("The scheduled pipeline will keep these companies up to date from now on.")


if __name__ == "__main__":
    main()
