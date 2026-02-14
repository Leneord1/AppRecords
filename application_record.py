from __future__ import annotations

import csv
import datetime
from pathlib import Path
from typing import Optional, Union


class ApplicationRecord:

    CSV_HEADER = ["timestamp", "company_name", "application_id"]

    def __init__(
        self,
        timestamp: Optional[Union[str, datetime.datetime]] = None,
        company_name: str = "",
        application_id: str = "",
    ) -> None:
        # default to current UTC time if not provided
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)
        self._timestamp = self._to_iso_utc(timestamp)
        self._company_name = str(company_name)
        self._application_id = str(application_id)

    # --- timestamp property ---
    @property
    def timestamp(self) -> str:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: Union[str, datetime.datetime]) -> None:
        self._timestamp = self._to_iso_utc(value)


    # --- company_name property ---
    @property
    def company_name(self) -> str:
        return self._company_name

    @company_name.setter
    def company_name(self, value: str) -> None:
        self._company_name = str(value)


    # --- application_id property ---
    @property
    def application_id(self) -> str:
        return self._application_id

    @application_id.setter
    def application_id(self, value: str) -> None:
        self._application_id = str(value)


    # --- helpers ---
    def to_csv_row(self) -> list:
        """Return a list suitable for csv.writer.writerow."""
        return [self.timestamp, self.company_name, self.application_id]

    def append_to_csv(self, file_path: Union[str, Path]) -> None:

        path = Path(file_path)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        write_header = not path.exists() or path.stat().st_size == 0

        # Use newline="" to let csv module handle newlines correctly across platforms
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            if write_header:
                writer.writerow(self.CSV_HEADER)
            writer.writerow(self.to_csv_row())

    @staticmethod
    def _to_iso_utc(value: Union[str, datetime.datetime]) -> str:
        if isinstance(value, datetime.datetime):
            # convert to UTC timezone-aware and format without offset, append Z
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            else:
                dt = dt.astimezone(datetime.timezone.utc)
            # format as YYYY-MM-DDThh:mm:ssZ
            return dt.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"
        elif isinstance(value, str):
            return value
        else:
            raise TypeError("timestamp must be a datetime or ISO8601 string")

    def __repr__(self) -> str:
        return (
            f"ApplicationRecord(timestamp={self.timestamp!r}, "
            f"company_name={self.company_name!r}, application_id={self.application_id!r})"
        )
