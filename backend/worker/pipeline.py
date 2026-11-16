"""MVP pipeline: collect CS jobs from Greenhouse, Lever and Ashby -> Supabase.

Run (from backend/worker, with the virtual environment turned on):
    python pipeline.py

What it does, for every supported company in the `companies` table:
  1. Collect   - download the company's job list (with descriptions)
  2. Clean up  - keep U.S., early-career-friendly CS roles; reshape to our columns
  3. Save      - add new jobs, refresh ones we already have (no duplicates)
  4. Close     - mark jobs we haven't seen for CLOSE_AFTER_DAYS as closed

Needs: .env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY, and migrations 000-002 run.
"""
import argparse
import concurrent.futures
import hashlib
import html
import os
import re
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from supabase import create_client

from notifier import notify_new_jobs, notify_target_role_matches

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Greenhouse companies to add to the `companies` table if they aren't there yet.
# Format: "Display name": "greenhouse slug" (from job-boards.greenhouse.io/<slug>).
# A company that has moved off Greenhouse is skipped with a warning, so it's
# safe to leave a few that don't work. Add more any time.
STARTER_COMPANIES = {
    "Stripe": "stripe",
    "Airbnb": "airbnb",
    "Discord": "discord",
    "Figma": "figma",
    "Databricks": "databricks",
    "Robinhood": "robinhood",
    "Coinbase": "coinbase",
    "Cloudflare": "cloudflare",
    "Datadog": "datadog",
    "Reddit": "reddit",
    "Dropbox": "dropbox",
    "Pinterest": "pinterest",
    "Lyft": "lyft",
    "Instacart": "instacart",
    "Twilio": "twilio",
    "Affirm": "affirm",
    "Airtable": "airtable",
    "Asana": "asana",
    "Brex": "brex",
    "Chime": "chime",
    "Cockroach Labs": "cockroachlabs",
    "Duolingo": "duolingo",
    "Elastic": "elastic",
    "GitLab": "gitlab",
    "HubSpot": "hubspotjobs",
    "Klaviyo": "klaviyo",
    "MongoDB": "mongodb",
    "Okta": "okta",
    "Roblox": "roblox",
    "Rubrik": "rubrik",
    "Samsara": "samsara",
    "Scale AI": "scaleai",
    "SoFi": "sofi",
    "Squarespace": "squarespace",
    "Toast": "toast",
    "Twitch": "twitch",
    "Verkada": "verkada",
    "SingleStore": "singlestore",
    "Vercel": "vercel",
    "Gusto": "gusto",
    "Ramp": "ramp",
}

CLOSE_AFTER_DAYS = 2  # jobs not seen for this long get marked closed
BATCH_SIZE = 200      # how many rows to send to Supabase at once
DOWNLOAD_WORKERS = 8  # job boards downloaded at the same time
DOWNLOAD_CHUNK = 32   # boards downloaded ahead of the database writes, to cap memory use

# A title must contain one of these (whole words) to count as a CS job.
# Broad words like "data", "security", "intern" or "engineer" only count inside
# a phrase: alone they also match "Data Migration Consultant", "Physical
# Security Associate", "Accounting Intern" or "Welding Engineer". Interns and
# new grads still qualify through their role, e.g. "Software Engineer Intern".
CS_WORDS = [
    # Software roles
    "software", "developer", "programmer", "swe", "member of technical staff",
    "backend", "back end", "frontend", "front end", "full stack", "fullstack",
    "mobile", "ios", "android", "firmware", "embedded", "web",
    "devops", "sre", "site reliability", "cloud", "kubernetes", "distributed systems",
    "compiler", "kernel", "graphics", "computing",
    # Engineer titles that are software work at tech companies
    "forward deployed", "founding engineer", "product engineer", "ai engineer", "llm",
    "research engineer", "infrastructure engineer", "platform engineer",
    "data engineer", "analytics engineer", "data mining", "network engineer",
    "security engineer", "qa", "quality assurance", "test automation",
    # Data, ML and research
    "machine learning", "ml", "deep learning", "computer vision", "nlp",
    "data science", "data scientist", "data analyst", "data engineering",
    "research scientist", "research science", "applied scientist", "ai research", "ai researcher",
    "analytics intern", "information technology",
    # Security and infrastructure
    "security analyst", "security researcher", "security engineering", "security operations",
    "cybersecurity", "cyber security", "application security",
    "infrastructure engineering", "platform engineering",
]

# ...and must NOT contain any of these (leadership, or not really a CS role)
EXCLUDE_WORDS = [
    "lead", "manager", "director", "head", "supervisor", "vp", "vice president", "architect",
    "sales", "solutions", "account", "recruiter", "recruiting", "counsel",
    "marketing", "designer", "technician",
]

# Too senior, unless the title says it is an early-career role
# ("Senior Machine Learning Engineer - PhD Early Career").
SENIOR_WORDS = [
    "senior", "sr", "staff", "principal", "distinguished", "ii", "iii", "iv",
    "mid level", "mid-level", "midlevel", "experienced",
]
EARLY_CAREER_WORDS = [
    "early career", "new grad", "new graduate", "university grad", "university graduate",
    "recent graduate", "college grad", "campus", "entry level", "entry-level", "junior",
    "apprentice", "apprenticeship", "intern", "internship", "co-op", "residency",
]

# A plain title ("Software Engineer") can be any level, so the description
# decides: a job asking for more than this many years of experience is not
# early career. "3+ years of experience", "2-4 years of professional software
# experience" and "minimum 5 years experience" are all read; a range counts
# by its low end, and the smallest number in the description wins, so a job
# that also says "1+ years with AWS" is kept.
MAX_YEARS_FOR_EARLY_CAREER = 2
YEARS_PATTERN = re.compile(
    r"\b(\d{1,2})\s*\+?\s*(?:(?:-|\u2013|to)\s*\d{1,2}\s*\+?\s*)?years?"
    r"(?:\s+of)?(?:\s+[\w/&-]+){0,4}?\s+experience",
    re.IGNORECASE,
)

# Engineering fields outside software. A title naming one of these is dropped
# even if it also has a CS phrase ("Network Engineer, Fiber Optic Layout",
# "Embedded Controls GNC Engineer"), unless it names software work too
# ("Software Engineer, Hardware Health" is kept). Words that also appear in
# software titles are written as phrases ("audio engineer", not "audio").
OTHER_ENGINEERING_WORDS = [
    # Mechanical, vehicles and aerospace
    "mechanical", "mechatronics", "aerospace", "aeronautical", "astronautical", "avionics",
    "propulsion", "automotive", "chassis", "powertrain", "body structures", "vehicle safety",
    "cae", "cad", "thermal", "hvac", "fire protection", "controls engineer",
    # Electrical and chip design
    "electrical", "hardware", "hw", "analog", "rf", "pcb", "pcba", "asic", "fpga", "rtl",
    "physical design", "design verification", "signal integrity", "power electronics",
    "optical", "photonics", "battery",
    # Civil, chemical, materials and other physical fields
    "civil engineer", "structural", "geotechnical", "environmental engineer", "site engineer",
    "chemical", "process engineer", "materials", "metallurgical", "biomedical", "bioengineer",
    "nuclear", "petroleum", "mining engineer", "agricultural", "marine", "naval", "packaging",
    "manufacturing", "industrial", "audio engineer",
    # Test, quality, supply and site roles at hardware companies
    "test engineer", "test engineering", "quality engineer", "quality engineering",
    "integration and test", "integration & test", "launch engineer", "structures",
    "supplier", "supply chain", "production engineer", "site development",
    "facilities", "electromagnetic", "gnc", "guidance", "fiber", "rfic",
    "cnc", "cmm", "edm", "solar", "welding", "outside plant", "antenna",
]
SOFTWARE_WORK_WORDS = [
    "software", "firmware", "embedded", "ml", "machine learning",
    "data engineer", "data engineering", "data scientist", "data science", "data mining",
]

US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
US_HINTS = [
    "united states", "usa", "u.s.", "new york", "nyc", "san francisco", "seattle",
    "chicago", "austin", "boston", "los angeles", "denver", "atlanta", "raleigh",
    "durham", "washington", "miami", "dallas", "portland", "philadelphia",
    "pittsburgh", "salt lake", "san jose", "mountain view", "palo alto", "sunnyvale",
    "bay area", "remote - us", "remote, us", "remote (us",
]
NON_US_HINTS = [
    "canada", "toronto", "vancouver", "london", "united kingdom", "uk", "dublin",
    "ireland", "india", "bengaluru", "bangalore", "hyderabad", "singapore", "tokyo",
    "japan", "germany", "berlin", "munich", "paris", "france", "australia",
    "sydney", "melbourne", "mexico", "brazil", "são paulo", "sao paulo",
    "amsterdam", "netherlands", "spain", "madrid", "barcelona", "poland",
    "warsaw", "emea", "apac", "latam", "europe",
]

load_dotenv()


def get_client():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


# ---------------------------------------------------------------------------
# Helpers (no database or internet needed, so they're easy to test)
# ---------------------------------------------------------------------------

def has_word(text: str, words: list[str]) -> bool:
    """True if any of the words/phrases appears as a whole word in text."""
    text = text.lower()
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def is_cs_role(title: str) -> bool:
    if not has_word(title, CS_WORDS) or has_word(title, EXCLUDE_WORDS):
        return False
    # "Member of Technical Staff" is a standard software title at several AI
    # companies; its "staff" is not the seniority level that SENIOR_WORDS means.
    without_mts = re.sub(r"\bmember of technical staff\b", "", title, flags=re.IGNORECASE)
    if has_word(without_mts, SENIOR_WORDS) and not has_word(title, EARLY_CAREER_WORDS):
        return False
    return not has_word(title, OTHER_ENGINEERING_WORDS) or has_word(title, SOFTWARE_WORK_WORDS)


def years_of_experience(description: str) -> int | None:
    """Smallest number of years of experience the description asks for, or None."""
    years = [int(number) for number in YEARS_PATTERN.findall(description or "") if int(number) <= 15]
    return min(years) if years else None


def is_early_career(title: str, description: str) -> bool:
    """Interns and new grads always count; otherwise the job must not ask for
    more than MAX_YEARS_FOR_EARLY_CAREER years (or must not say)."""
    if has_word(title, EARLY_CAREER_WORDS):
        return True
    years = years_of_experience(description)
    return years is None or years <= MAX_YEARS_FOR_EARLY_CAREER


def is_us_location(location: str) -> bool:
    lower = location.lower()
    if has_word(lower, US_HINTS):
        return True
    state_codes = re.findall(r"(?:,|\s-)\s*([A-Z]{2})\b", location)
    if any(code in US_STATE_CODES for code in state_codes):
        return True
    if has_word(lower, NON_US_HINTS):
        return False
    # Plain "Remote" (no country mentioned): keep it
    return "remote" in lower


def guess_work_mode(title: str, location: str) -> str:
    text = f"{title} {location}".lower()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    if location and location != "Unknown":
        return "in_person"
    return "unknown"


def html_to_text(content: str) -> str:
    """Turn HTML or escaped HTML descriptions into plain text."""
    if not content:
        return ""
    text = html.unescape(content)  # "&lt;p&gt;" -> "<p>"
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n• ", text)
    text = re.sub(r"<[^>]+>", "", text)  # remove remaining tags
    text = html.unescape(text)           # "&amp;" -> "&"
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()[:20000]


def make_fingerprint(company_id: int, title: str, location: str) -> str:
    """Same company + title + location always gives the same fingerprint."""
    text = f"{company_id}|{title.strip().lower()}|{location.strip().lower()}"
    return hashlib.sha256(text.encode()).hexdigest()


def clean_up(raw_jobs: list[dict], company_id: int, now: datetime, source: str = "greenhouse") -> list[dict]:
    """Reshape normalized ATS jobs to match our `jobs` table and drop unwanted roles."""
    rows = {}
    for job in raw_jobs:
        title = (job.get("title") or "").strip()
        location = ((job.get("location") or {}).get("name") or "Unknown").strip()
        if not title or not job.get("absolute_url") or not is_cs_role(title) or not is_us_location(location):
            continue
        fingerprint = make_fingerprint(company_id, title, location)
        if fingerprint in rows:  # same job listed twice in one download: keep the first
            continue
        description = html_to_text(job.get("content", ""))
        if not is_early_career(title, description):
            continue
        posted = job.get("first_published") or job.get("updated_at") or now.isoformat()
        rows[fingerprint] = {
            "company_id": company_id,
            "title": title,
            "location": location,
            "url": job["absolute_url"],
            "posted_at": posted[:10],
            "description": description,
            "work_mode": guess_work_mode(title, location),
            "source": source,
            "dedupe_hash": fingerprint,
            "is_open": True,
            "last_seen_at": now.isoformat(),
        }
    return list(rows.values())


# ---------------------------------------------------------------------------
# Database + internet steps
# ---------------------------------------------------------------------------

def seed_companies(supabase) -> None:
    rows = [
        {"name": name, "ats_type": "greenhouse", "ats_slug": slug}
        for name, slug in STARTER_COMPANIES.items()
    ]
    supabase.table("companies").upsert(rows, on_conflict="name", ignore_duplicates=True).execute()


def guess_logo_url(slug: str) -> str:
    """A company's ATS slug is usually its name, e.g. "stripe" -> stripe.com.
    Google's public, no-auth favicon service returns a generic placeholder
    icon (not a broken deploy) for a wrong guess or a domain with no favicon."""
    return f"https://www.google.com/s2/favicons?domain={slug}.com&sz=128"


def backfill_company_logos(supabase) -> int:
    """Any ATS company without a stored logo yet, not just the starter
    list, so companies added later (by the team or a future admin UI) also
    get one without this file needing a per-company update."""
    missing = (
        supabase.table("companies").select("id, ats_slug")
        .is_("logo_url", "null").execute().data
    )
    updates = [{"id": row["id"], "logo_url": guess_logo_url(row["ats_slug"])} for row in missing if row.get("ats_slug")]
    for row in updates:
        # Always an update to an existing row; `id` is a GENERATED ALWAYS identity
        # column, so upsert's INSERT clause would reject supplying it explicitly.
        supabase.table("companies").update({"logo_url": row["logo_url"]}).eq("id", row["id"]).execute()
    return len(updates)


def collect_greenhouse(slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
        raise ValueError(f"Unexpected Greenhouse response for board {slug!r}")
    return jobs


def collect_lever(slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    postings = response.json()
    if not isinstance(postings, list) or not all(isinstance(posting, dict) for posting in postings):
        raise ValueError(f"Unexpected Lever response for board {slug!r}")

    jobs = []
    for posting in postings:
        categories = posting.get("categories") or {}
        created_at = posting.get("createdAt")
        if created_at is not None:
            try:
                posted_at = datetime.fromtimestamp(float(created_at) / 1000, timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError, OSError) as error:
                raise ValueError(f"Invalid Lever posting date on board {slug!r}") from error
        else:
            posted_at = None
        jobs.append({
            "title": posting.get("text"),
            "location": {"name": categories.get("location") or "Unknown"},
            "absolute_url": posting.get("hostedUrl") or posting.get("applyUrl"),
            "first_published": posted_at,
            "content": posting.get("description") or posting.get("descriptionPlain") or "",
        })
    return jobs


def collect_ashby(slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
        raise ValueError(f"Unexpected Ashby response for board {slug!r}")

    return [
        {
            "title": job.get("title"),
            "location": {"name": job.get("location") or ("Remote" if job.get("isRemote") else "Unknown")},
            "absolute_url": job.get("jobUrl") or job.get("applyUrl"),
            "first_published": job.get("publishedAt"),
            "content": job.get("descriptionHtml") or job.get("descriptionPlain") or "",
        }
        for job in jobs
    ]


COLLECTORS = {
    "greenhouse": collect_greenhouse,
    "lever": collect_lever,
    "ashby": collect_ashby,
}


def collect(ats_type: str, slug: str) -> list[dict]:
    """Download and normalize job postings from a supported applicant tracking system."""
    collector = COLLECTORS.get(ats_type)
    if collector is None:
        raise ValueError(f"Unsupported ATS type: {ats_type}")
    return collector(slug)


def download(company: dict, now: datetime) -> tuple[dict, int, list[dict], Exception | None]:
    """Download and filter one company's board. Runs in a worker thread, so it
    must not touch the database. Filtering here drops non-CS descriptions early."""
    try:
        raw_jobs = collect(company["ats_type"], company["ats_slug"])
    except (requests.RequestException, ValueError) as error:
        return company, 0, [], error
    return company, len(raw_jobs), clean_up(raw_jobs, company["id"], now, source=company["ats_type"]), None


def download_all(companies: list[dict], now: datetime):
    """Yield download results in order, fetching several boards at once."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as pool:
        for start in range(0, len(companies), DOWNLOAD_CHUNK):
            chunk = companies[start:start + DOWNLOAD_CHUNK]
            yield from pool.map(lambda company: download(company, now), chunk)


def fetch_companies(supabase) -> list[dict]:
    """Every company with a job board, read in pages (Supabase returns at most 1,000 rows per request)."""
    companies, page_size, offset = [], 1000, 0
    while True:
        page = (
            supabase.table("companies").select("id, name, ats_type, ats_slug, logo_url")
            .order("name").range(offset, offset + page_size - 1).execute().data
        )
        companies += page
        if len(page) < page_size:
            return [company for company in companies if company.get("ats_type") and company.get("ats_slug")]
        offset += page_size


def save(supabase, rows: list[dict], company_id: int) -> list[dict]:
    """Upsert jobs for a company; return the rows that are newly added (not merely refreshed)."""
    # Read in pages: Supabase returns at most 1,000 rows per request by default,
    # so a single request could miss saved jobs and make old jobs look new.
    already_saved = set()
    page_size = 1000
    offset = 0
    while True:
        page = (
            supabase.table("jobs").select("dedupe_hash").eq("company_id", company_id)
            .order("id").range(offset, offset + page_size - 1).execute().data
        )
        already_saved.update(row["dedupe_hash"] for row in page)
        if len(page) < page_size:
            break
        offset += page_size
    new_rows = []
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        result = supabase.table("jobs").upsert(batch, on_conflict="dedupe_hash").execute()
        new_rows += [row for row in result.data if row["dedupe_hash"] not in already_saved]
    return new_rows


def close_old_jobs(supabase, company_id: int, now: datetime) -> int:
    cutoff = (now - timedelta(days=CLOSE_AFTER_DAYS)).isoformat()
    result = (
        supabase.table("jobs")
        .update({"is_open": False})
        .eq("company_id", company_id)
        .eq("is_open", True)
        .lt("last_seen_at", cutoff)
        .execute()
    )
    return len(result.data)


def find_closing_soon_jobs(supabase, company_id: int, now: datetime) -> list[dict]:
    """Still open but not seen in the back half of its countdown to close_old_jobs.
    Call before close_old_jobs so these jobs are still is_open when queried."""
    window_start = (now - timedelta(days=CLOSE_AFTER_DAYS)).isoformat()
    window_end = (now - timedelta(days=CLOSE_AFTER_DAYS - 1)).isoformat()
    result = (
        supabase.table("jobs")
        .select("id, title, url, location, posted_at, company_id")
        .eq("company_id", company_id)
        .eq("is_open", True)
        .gte("last_seen_at", window_start)
        .lt("last_seen_at", window_end)
        .execute()
    )
    return result.data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-skills", action="store_true", help="Extract stored skill mentions after collection (requires migration 005)")
    parser.add_argument("--skill-limit", type=int, default=50, choices=range(1, 501), metavar="1..500")
    args = parser.parse_args()
    supabase = get_client()
    now = datetime.now(timezone.utc)
    seed_companies(supabase)
    backfill_company_logos(supabase)

    companies = fetch_companies(supabase)

    totals = {"kept": 0, "new": 0, "closed": 0, "failed": 0, "notified": 0, "emailed": 0,
              "closing_soon": 0, "role_matched": 0}
    all_new_jobs = []
    all_closing_soon_jobs = []
    for company, raw_count, rows, error in download_all(companies, now):
        name, ats_type = company["name"], company["ats_type"]
        if error is not None:
            print(f"  ! {name}: skipped, couldn't collect from {ats_type} ({error})")
            totals["failed"] += 1
            continue

        new_rows = save(supabase, rows, company["id"])
        closing_soon_jobs = find_closing_soon_jobs(supabase, company["id"], now)
        closed_count = close_old_jobs(supabase, company["id"], now)
        notify_result = notify_new_jobs(supabase, company["id"], name, new_rows, now, kind="new_posting", company_logo_url=company.get("logo_url"))
        closing_notify_result = notify_new_jobs(supabase, company["id"], name, closing_soon_jobs, now, kind="closing_soon", company_logo_url=company.get("logo_url"))
        all_new_jobs += new_rows
        all_closing_soon_jobs += closing_soon_jobs
        totals["kept"] += len(rows)
        totals["new"] += len(new_rows)
        totals["closed"] += closed_count
        totals["closing_soon"] += len(closing_soon_jobs)
        totals["notified"] += notify_result["notified"] + closing_notify_result["notified"]
        totals["emailed"] += notify_result["emailed"] + closing_notify_result["emailed"]
        print(f"  {name}: {raw_count} downloaded, {len(rows)} kept, "
              f"{len(new_rows)} new, {len(closing_soon_jobs)} closing soon, {closed_count} closed")

    role_match_result = notify_target_role_matches(supabase, all_new_jobs, now, kind="new_posting")
    closing_role_match_result = notify_target_role_matches(supabase, all_closing_soon_jobs, now, kind="closing_soon")
    totals["role_matched"] = role_match_result["notified"] + closing_role_match_result["notified"]

    print(f"\nDone. {totals['kept']} jobs kept, {totals['new']} new, {totals['closing_soon']} closing soon, "
          f"{totals['closed']} closed, {totals['failed']} companies skipped, "
          f"{totals['notified']} notifications created, {totals['emailed']} instant emails sent, "
          f"{totals['role_matched']} target-role notifications created.")

    if args.with_skills:
        import logging
        from skills import run_extraction
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        result = run_extraction(supabase, args.skill_limit)
        if result["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
