import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

import pdfplumber
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet


# Constants
SPREADSHEET_PATH = Path("bills.xlsx")
MAX_BILL_AMOUNT = 100000
MIN_BILL_AMOUNT = 0.01
MAX_COMPANY_NAME_LENGTH = 50
EXCEL_SHEET_NAME_MAX_LENGTH = 31

# Month name patterns (abbreviations and full names)
MONTH_PATTERN = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)

MONTH_NAME_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

MONTH_NUMBER_TO_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

COMPANY_PATTERNS = {
    r"consolidated\s+edison|con\s*ed": "ConEdison",
    r"national\s+grid": "National Grid",
    r"bank\s+of\s+america|bofa": "Bank of America",
}


@dataclass
class BillInfo:
    company: str
    month: int
    year: int
    amount: float


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def detect_company(text: str) -> str:
    """
    Detect company name from bill text.
    Tries known patterns first, then falls back to first non-empty line.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lower_text = text.lower()
    
    for pattern, name in COMPANY_PATTERNS.items():
        if re.search(pattern, lower_text, re.IGNORECASE):
            return name
    
    if lines:
        return re.sub(r"\s+", " ", lines[0])[:MAX_COMPANY_NAME_LENGTH]
    return "Unknown"


def month_number_to_name(month: int) -> str:
    """Convert month number (1-12) to full month name."""
    return MONTH_NUMBER_TO_NAME.get(month, "Unknown")


def _extract_month_year_from_match(match, month_idx: int, year_idx: int) -> Tuple[int, int]:
    """Extract month and year from a regex match group."""
    month_str = match.group(month_idx).lower()
    year_str = match.group(year_idx)
    month = MONTH_NAME_MAP[month_str]
    year = int(year_str)
    return month, year


def detect_month_year(text: str) -> Optional[Tuple[int, int]]:
    """
    Detect billing month and year from text.
    Tries multiple patterns in order of specificity.
    """
    # Pattern 1: "Billing period: Jul 14, 2025 to Aug 05, 2025"
    pattern = re.compile(
        rf"Billing period:\s+({MONTH_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})\s+to\s+"
        rf"({MONTH_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return _extract_month_year_from_match(match, 1, 3)

    # Pattern 2: "August 28 - September 27, 2021" (dash separator)
    pattern = re.compile(
        rf"({MONTH_PATTERN})\s+(\d{{1,2}})\s*-\s*({MONTH_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return _extract_month_year_from_match(match, 1, 5)

    # Pattern 3: "Jul 15, 2025 to Aug 13, 2025" (no prefix)
    pattern = re.compile(
        rf"({MONTH_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})\s+to\s+"
        rf"({MONTH_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return _extract_month_year_from_match(match, 1, 3)

    # Pattern 4: Numeric billing period "08-14-2025 to 09-13-2025"
    pattern = re.compile(
        r"Billing period[:\s]*(\d{1,2})[/-](\d{1,2})[/-](\d{4}).{0,40}?(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        month = int(match.group(1))
        year = int(match.group(3))
        return month, year

    # Pattern 5: "Statement Date: August 2021"
    pattern = re.compile(
        rf"(?:statement\s+date|billing\s+period|statement\s+period)[:\s]+({MONTH_PATTERN})\s+(\d{{4}})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return _extract_month_year_from_match(match, 1, 2)

    # Pattern 6: "August 2021" or "Aug 2021" (month name + year)
    pattern = re.compile(rf"\b({MONTH_PATTERN})\s+(\d{{4}})", re.IGNORECASE)
    for match in pattern.finditer(text):
        return _extract_month_year_from_match(match, 1, 2)

    # Pattern 7: "10/2025" or "10-2025" (numeric month/year)
    pattern = re.compile(r"\b(0?[1-9]|1[0-2])[/-](\d{4})\b")
    for match in pattern.finditer(text):
        month = int(match.group(1))
        year = int(match.group(2))
        return month, year

    return None


def clean_amount_str(amount_str: str) -> Optional[float]:
    """Clean and convert amount string to float."""
    try:
        cleaned = re.sub(r"[^\d.\-]", "", amount_str)
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _is_phone_number(context: str) -> bool:
    """Check if context looks like a phone number (has digit-dash pattern)."""
    return bool(re.search(r'\d-\d', context))


def _extract_amounts_from_line(line: str, currency_pattern, decimal_pattern) -> list[float]:
    """Extract currency amounts from a line of text."""
    amounts = []
    
    # Try currency format ($XX.XX)
    for match in currency_pattern.finditer(line):
        amt = clean_amount_str(match.group(1))
        if amt and amt < MAX_BILL_AMOUNT:
            amounts.append(amt)
    
    # Try decimal format (XX.XX)
    for match in decimal_pattern.finditer(line):
        start, end = match.span()
        context = line[max(0, start - 5):min(len(line), end + 5)]
        if _is_phone_number(context):
            continue
        amt = clean_amount_str(match.group(1))
        if amt and MIN_BILL_AMOUNT <= amt < MAX_BILL_AMOUNT:
            amounts.append(amt)
    
    return amounts


def detect_amount(text: str) -> Optional[float]:
    """
    Detect bill amount from text.
    Prefers amounts near keywords like 'Total Amount Due', then falls back to all amounts.
    """
    lines = text.splitlines()
    currency_pattern = re.compile(r"\$\s*(\d[\d,]*\.\d{2})")
    decimal_pattern = re.compile(r"(\d[\d,]*\.\d{2})")
    keyword_pattern = re.compile(
        r"(total\s+amount\s+due|amount\s+due|total\s+due|current\s+charges|"
        r"amount\s+due\s+now|new\s+balance|statement\s+balance|payment\s+due|balance\s+due)",
        re.IGNORECASE,
    )

    # First pass: look near keywords
    for idx, line in enumerate(lines):
        if keyword_pattern.search(line):
            amounts = []
            for j in range(max(0, idx - 1), min(len(lines), idx + 2)):
                amounts.extend(_extract_amounts_from_line(lines[j], currency_pattern, decimal_pattern))
            if amounts:
                return max(amounts)

    # Fallback: collect all amounts
    all_amounts = []
    for line in lines:
        all_amounts.extend(_extract_amounts_from_line(line, currency_pattern, decimal_pattern))
    
    return max(all_amounts) if all_amounts else None


def parse_bill(pdf_path: Path) -> BillInfo:
    """Parse a bill PDF and extract company, date, and amount."""
    text = extract_text_from_pdf(pdf_path)
    company = detect_company(text)
    
    month_year = detect_month_year(text)
    month, year = (month_year if month_year else (1, 1970))
    
    amount = detect_amount(text) or 0.0
    
    return BillInfo(company=company, month=month, year=year, amount=amount)


def get_or_create_workbook(path: Path) -> Workbook:
    """Get existing workbook or create a new one."""
    return load_workbook(path) if path.exists() else Workbook()


def normalize_sheet_name(company: str) -> str:
    """Normalize company name for use as Excel sheet name."""
    unsafe_chars = r'[:\\/*?\[\]]'
    safe_name = re.sub(unsafe_chars, "_", company).strip() or "Unknown"
    sheet_name = f"{safe_name}_bill"
    return sheet_name[:EXCEL_SHEET_NAME_MAX_LENGTH]


def get_or_create_company_sheet(wb: Workbook, company: str) -> Worksheet:
    """Get or create a worksheet for the given company."""
    sheet_name = normalize_sheet_name(company)
    
    if sheet_name in wb.sheetnames:
        return wb[sheet_name]
    
    # Replace default sheet if it's empty, otherwise create new
    if len(wb.sheetnames) == 1 and wb.active.max_row == 1 and wb.active.max_column == 1:
        ws = wb.active
        ws.title = sheet_name
    else:
        ws = wb.create_sheet(title=sheet_name)
    
    ws.append(["month", "year", "amount"])
    return ws


def append_bill_to_spreadsheet(info: BillInfo, path: Optional[Path] = None) -> None:
    """Append bill information to the spreadsheet."""
    if path is None:
        path = SPREADSHEET_PATH
    
    wb = get_or_create_workbook(path)
    ws = get_or_create_company_sheet(wb, info.company)
    month_name = month_number_to_name(info.month)
    ws.append([month_name, info.year, info.amount])
    wb.save(path)


def iter_pdf_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Iterate over all PDF files in the given paths."""
    for path in paths:
        if path.is_dir():
            yield from sorted(path.rglob("*.pdf"))
        elif path.is_file() and path.suffix.lower() == ".pdf":
            yield path


def process_bills(paths: Iterable[Path]) -> None:
    """Process all PDF bills and save to spreadsheet."""
    for pdf_path in iter_pdf_files(paths):
        print(f"Processing {pdf_path} ...")
        info = parse_bill(pdf_path)
        print(
            f"  Parsed -> company={info.company!r}, month={info.month}, "
            f"year={info.year}, amount={info.amount}"
        )
        append_bill_to_spreadsheet(info)
        print("  Saved to spreadsheet.")


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Main entry point."""
    global SPREADSHEET_PATH
    
    parser = argparse.ArgumentParser(
        description="BillReader: parse bill PDFs and record them into a spreadsheet.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more PDF files or directories containing PDFs.",
    )
    parser.add_argument(
        "--spreadsheet",
        type=str,
        default=str(SPREADSHEET_PATH),
        help="Path to the output spreadsheet (default: bills.xlsx).",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    SPREADSHEET_PATH = Path(args.spreadsheet)
    process_bills(Path(p) for p in args.paths)


if __name__ == "__main__":
    main()
