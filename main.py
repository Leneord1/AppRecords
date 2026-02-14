from __future__ import annotations

from pathlib import Path
import argparse
import datetime
import sys

from typing import Optional
from application_record import ApplicationRecord

# Try to import Streamlit if it's available. Keep it optional so the script
# can still run in console environments where Streamlit isn't installed.
try:
    import streamlit as st  # type: ignore
except Exception:
    st = None


def parse_timestamp(s: str) -> datetime.datetime:

    s = s.strip()
    if not s:
        return datetime.datetime.now(datetime.timezone.utc)

    try:
        # datetime.fromisoformat doesn't accept a trailing 'Z', so convert it.
        if s.endswith("Z"):
            # replace Z with +00:00 which fromisoformat understands
            s2 = s[:-1] + "+00:00"
            return datetime.datetime.fromisoformat(s2).astimezone(datetime.timezone.utc).replace(tzinfo=None)
        else:
            return datetime.datetime.fromisoformat(s)
    except Exception:
        print("Warning: couldn't parse timestamp; using current UTC time.")
        return datetime.datetime.now(datetime.timezone.utc)


def prompt_for_record() -> Optional[ApplicationRecord]:
    # Console-based prompting for interactive mode
    company = input("Company name (leave empty to finish): ").strip()
    if not company:
        return None

    application_id = input("Application ID: ").strip()
    timestamp_raw = input("Timestamp (ISO8601, press Enter to use current UTC): ").strip()
    ts = parse_timestamp(timestamp_raw)

    return ApplicationRecord(timestamp=ts, company_name=company, application_id=application_id)


def streamlit_mode(out: Path) -> None:
    assert st is not None, "Streamlit not available"

    st.title("Application Records")
    st.write("Add a job application record")

    company = st.text_input("Company name", key="company")
    application_id = st.text_input("Application ID", key="application_id")
    timestamp_raw = st.text_input("Timestamp (ISO8601, leave empty to use current UTC)", key="timestamp")

    if st.button("Append"):
        if not company:
            st.warning("Company name cannot be empty.")
        else:
            ts = parse_timestamp(timestamp_raw or "")
            rec = ApplicationRecord(timestamp=ts, company_name=company, application_id=application_id)
            try:
                rec.append_to_csv(out)
                st.success(f"Appended record for '{company}' to {out}")
            except Exception as e:
                st.error(f"Failed to append record: {e}")

    st.write("---")
    st.write("CSV file:", out)

    if out.exists():
        if st.button("Show CSV"):
            import csv
            with out.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    st.table(rows)
                else:
                    st.write("CSV is empty")
    else:
        st.info("CSV file does not exist yet. Append a record to create it.")


def interactive_mode(out: Path) -> None:
    print("Entering interactive mode. Provide records one by one.")
    print("Leave the company name blank to finish and exit.")

    while True:
        rec = prompt_for_record()
        if rec is None:
            print("Finished input. Exiting.")
            break
        rec.append_to_csv(out)
        print(f"Appended record for '{rec.company_name}' to {out}")



def main() -> None:
    parser = argparse.ArgumentParser(description="Append application records to a CSV file.")
    parser.add_argument("--output", "-o", default=None, help="Path to output CSV file (default: ./applications.csv)")
    parser.add_argument("--demo", action="store_true", help="Run non-interactive demo that writes two example records")
    args = parser.parse_args()

    out = Path(args.output) if args.output else Path(__file__).parent / "applications.csv"

    # If Streamlit is installed and we're running under the Streamlit scriptrunner,
    # prefer the Streamlit UI. We detect Streamlit runtime presence by checking
    # for the streamlit.scriptrunner module in sys.modules which Streamlit loads
    # when running the app. This avoids activating the web UI when someone runs
    # the script from the console while Streamlit is installed.
    if st is not None and "streamlit.runtime.scriptrunner" in sys.modules:
        streamlit_mode(out)
    else:
        interactive_mode(out)


if __name__ == "__main__":
    main()
# End of file
