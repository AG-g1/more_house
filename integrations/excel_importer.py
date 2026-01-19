# integrations/excel_importer.py
"""
Excel Importer for More House

Imports contract and room data from the occupancy report Excel files.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ExcelImporter:
    """
    Imports data from More House occupancy Excel reports.
    """

    # Expected column mappings from Excel to our schema
    BOOKED_UNITS_COLUMNS = {
        "Count": "row_number",
        "Name": "room_id",
        "Floor": "floor",
        "Sqm": "sqm",
        "Category": "category",
        "Rate Agreed": "weekly_rate",
        "Term Status": "term_status",
        "Residents Name": "resident_name",
        "Weeks Booked": "weeks_booked",
        "Start Date": "start_date",
        "End Date": "end_date",
        "Contract Value": "total_value",
        "Nationality": "nationality",
        "University": "university",
        "Level of Study": "level_of_study",
        "Source": "source",
        "Lead Source": "lead_source",
        "Payment Plan": "payment_plan",
    }

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        self.excel_file = pd.ExcelFile(file_path)
        logger.info(f"Loaded Excel file: {file_path}")
        logger.info(f"Available sheets: {self.excel_file.sheet_names}")

    def get_sheet_names(self) -> List[str]:
        """Return list of sheet names in the Excel file."""
        return self.excel_file.sheet_names

    def import_booked_units(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Import data from 'Booked Units' sheet.

        Returns:
            Tuple of (rooms, contracts) - lists of dictionaries
        """
        df = pd.read_excel(
            self.excel_file,
            sheet_name="Booked Units",
            header=5  # Header is on row 6 (0-indexed: 5)
        )

        # Rename columns to our schema
        df = df.rename(columns=self.BOOKED_UNITS_COLUMNS)

        # Extract unique rooms
        rooms = []
        seen_rooms = set()

        for _, row in df.iterrows():
            room_id = str(row.get("room_id", "")).strip()
            if not room_id or room_id in seen_rooms:
                continue

            seen_rooms.add(room_id)
            rooms.append({
                "room_id": room_id,
                "floor": str(row.get("floor", "")),
                "sqm": float(row.get("sqm", 0)) if pd.notna(row.get("sqm")) else None,
                "category": str(row.get("category", "")),
                "weekly_rate": float(row.get("weekly_rate", 0)) if pd.notna(row.get("weekly_rate")) else None,
            })

        # Extract contracts
        contracts = []
        for _, row in df.iterrows():
            room_id = str(row.get("room_id", "")).strip()
            resident_name = str(row.get("resident_name", "")).strip()

            if not room_id or not resident_name:
                continue

            # Parse dates
            start_date = self._parse_date(row.get("start_date"))
            end_date = self._parse_date(row.get("end_date"))

            if not start_date or not end_date:
                logger.warning(f"Skipping contract for {room_id}: invalid dates")
                continue

            contracts.append({
                "room_id": room_id,
                "resident_name": resident_name,
                "start_date": start_date,
                "end_date": end_date,
                "weekly_rate": float(row.get("weekly_rate", 0)) if pd.notna(row.get("weekly_rate")) else 0,
                "total_value": float(row.get("total_value", 0)) if pd.notna(row.get("total_value")) else 0,
                "weeks_booked": float(row.get("weeks_booked", 0)) if pd.notna(row.get("weeks_booked")) else 0,
                "payment_plan": str(row.get("payment_plan", "Installments")),
                "nationality": str(row.get("nationality", "")) if pd.notna(row.get("nationality")) else None,
                "university": str(row.get("university", "")) if pd.notna(row.get("university")) else None,
                "source": str(row.get("source", "")) if pd.notna(row.get("source")) else None,
                "status": "active",  # All booked units are active
            })

        logger.info(f"Imported {len(rooms)} unique rooms and {len(contracts)} contracts")
        return rooms, contracts

    def import_income_forecast(self) -> pd.DataFrame:
        """
        Import the Income Forecast sheet for detailed monthly breakdowns.
        """
        df = pd.read_excel(
            self.excel_file,
            sheet_name="Income Forecast",
            header=3
        )
        return df

    def import_cash_flow(self) -> Dict:
        """
        Import Cash Flow FC sheet.
        Returns structured cash flow data.
        """
        df = pd.read_excel(
            self.excel_file,
            sheet_name="Cash Flow FC",
            header=None
        )

        # Extract date headers (row 9)
        dates = df.iloc[9, 3:].dropna().tolist()

        # Extract key metrics
        cash_flow_data = {
            "dates": [d.strftime("%Y-%m") if hasattr(d, 'strftime') else str(d) for d in dates],
            "booked_cfs": df.iloc[13, 3:len(dates)+3].tolist(),
            "total_cash_flow": df.iloc[18, 3:len(dates)+3].tolist(),
            "opex": df.iloc[20, 3:len(dates)+3].tolist(),
        }

        return cash_flow_data

    def import_opex_budget(self) -> List[Dict]:
        """
        Import OPEX budget from Main Budget sheet.
        """
        df = pd.read_excel(
            self.excel_file,
            sheet_name="Main Budget AY25",
            header=None
        )

        # Extract monthly OPEX data
        # Row 8 has date headers, subsequent rows have expense categories
        opex_records = []

        # Date headers start at column 3
        date_row = df.iloc[8, 3:15].tolist()

        # Total OPEX might need to be calculated or found
        # For now, we'll use the structure we found
        return opex_records

    @staticmethod
    def _parse_date(value) -> Optional[date]:
        """Parse various date formats to date object."""
        if pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        return None


def import_from_excel(file_path: str) -> Dict:
    """
    Convenience function to import all data from an Excel file.

    Returns:
        Dict with 'rooms', 'contracts', 'cash_flow' keys
    """
    importer = ExcelImporter(file_path)
    rooms, contracts = importer.import_booked_units()

    return {
        "rooms": rooms,
        "contracts": contracts,
        "source_file": str(file_path),
        "imported_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Test import
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "/Users/alexgilts/Library/Mobile Documents/com~apple~CloudDocs/AG Work/SAV Group/More House - Occupancy Report - 29 Nov 2025 (with Forecast).xlsx"

    try:
        data = import_from_excel(file_path)
        print(f"\nImported {len(data['rooms'])} rooms")
        print(f"Imported {len(data['contracts'])} contracts")

        print("\nSample rooms:")
        for room in data['rooms'][:3]:
            print(f"  {room}")

        print("\nSample contracts:")
        for contract in data['contracts'][:3]:
            print(f"  {contract['room_id']}: {contract['resident_name']} ({contract['start_date']} to {contract['end_date']})")

    except FileNotFoundError as e:
        print(f"Error: {e}")
