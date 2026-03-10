from __future__ import annotations

import csv
import datetime
from pathlib import Path

import requests
import streamlit as st

from application_record import ApplicationRecord
from email_scraper import scrape_emails


# ── Constants ────────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "applications.csv"


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_timestamp(s: str) -> datetime.datetime:
    s = s.strip()
    if not s:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(s).astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def fetch_emails_from_url(url: str) -> list[str]:
    """Fetch a URL and return any email addresses found in the HTML."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    found = scrape_emails(response.text)
    return sorted({e[0] if isinstance(e, tuple) else e for e in found})


def load_csv() -> list[dict]:
    if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
        return []
    with CSV_PATH.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Job Application Tracker", page_icon="💼", layout="wide")

st.title("Job Application Tracker")

tab_add, tab_view = st.tabs(["Add Record", "View Records"])


# ── Tab 1: Add Record ─────────────────────────────────────────────────────────

with tab_add:
    st.subheader("New Application")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name *", placeholder="e.g. Acme Corp")
    with col2:
        application_id = st.text_input("Application ID *", placeholder="e.g. REQ-12345")

    timestamp_raw = st.text_input(
        "Timestamp (ISO 8601 — leave blank for current UTC time)",
        placeholder="e.g. 2026-03-10T14:00:00Z",
    )

    st.subheader("Recruiter Email")
    email_method = st.radio(
        "How would you like to add the recruiter email?",
        ["Enter manually", "Scrape from URL", "Skip"],
        horizontal=True,
    )

    recruiter_email = ""

    if email_method == "Enter manually":
        recruiter_email = st.text_input("Recruiter Email", placeholder="recruiter@company.com")

    elif email_method == "Scrape from URL":
        scrape_url = st.text_input("URL to scrape", placeholder="https://company.com/careers/contact")

        if st.button("🔍 Scrape Emails", disabled=not scrape_url):
            with st.spinner("Fetching page and scanning for emails…"):
                try:
                    emails = fetch_emails_from_url(scrape_url)
                    if emails:
                        st.session_state["scraped_emails"] = emails
                        st.success(f"Found {len(emails)} email(s).")
                    else:
                        st.session_state["scraped_emails"] = []
                        st.warning("No emails found at that URL.")
                except Exception as exc:
                    st.session_state["scraped_emails"] = []
                    st.error(f"Could not fetch URL: {exc}")

        scraped = st.session_state.get("scraped_emails", [])
        if scraped:
            recruiter_email = st.selectbox("Select email to use", scraped)

    st.divider()

    if st.button("Save Record", type="primary", disabled=not (company and application_id)):
        ts = parse_timestamp(timestamp_raw)
        rec = ApplicationRecord(
            timestamp=ts,
            company_name=company,
            application_id=application_id,
            recruiter_email=recruiter_email,
        )
        try:
            rec.append_to_csv(CSV_PATH)
            st.success(f"Record saved for **{company}** (`{application_id}`)")
            # Clear scraped emails after a successful save
            st.session_state.pop("scraped_emails", None)
        except Exception as exc:
            st.error(f"Failed to save record: {exc}")

    if not (company and application_id):
        st.caption("* Company Name and Application ID are required to save.")


# ── Tab 2: View Records ───────────────────────────────────────────────────────

with tab_view:
    st.subheader("All Application Records")

    rows = load_csv()

    col_info, col_download = st.columns([1, 1])
    with col_info:
        st.caption(f"📁 `{CSV_PATH}`  ·  **{len(rows)}** record(s)")

    if rows:
        with col_download:
            with CSV_PATH.open("rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name="applications.csv",
                    mime="text/csv",
                )

        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No records yet. Add your first application in the **➕ Add Record** tab.")