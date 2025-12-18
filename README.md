## BillReader

BillReader is a tool that helps you organize your bills automatically.  
Given a bill of almost any kind (utility, credit card, etc.), it extracts the key information  
and keeps a structured record of your payments in a single spreadsheet.

### What BillReader Does

- **Bill parsing**: Reads a bill and determines:
  - **Company / issuer** (e.g. electricity provider, credit card company)
  - **Billing month and year**
  - **Bill amount**
- **Spreadsheet management**:
  - Creates a **sheet/tab per company** in a single spreadsheet
  - Names each tab `companyname_bill` (where `companyname` is the actual issuer name)
  - Each tab contains **three columns**:
    - `month`
    - `year`
    - `amount`
- **Automatic updates**:
  - When you add a new bill from a company that already exists:
    - BillReader **appends a new row** to that company’s existing sheet
  - When you add a bill from a new company:
    - BillReader **creates a new sheet/tab** in the same spreadsheet and starts tracking bills there

### Example Workflow

1. **You upload a bill** (e.g. a PDF from your electricity company).
2. **BillReader extracts**:
   - Company: `Awesome Energy`
   - Month: `03`
   - Year: `2025`
   - Amount: `120.45`
3. **BillReader looks up** a tab named `Awesome Energy_bill`:
   - If it exists, it appends a new row: `03 | 2025 | 120.45`
   - If it does not exist, it creates the tab and adds the first row.

### Intended Benefits

- **Centralized tracking** of bills from multiple companies in one place.
- **Consistent format** (month, year, amount) to make it easy to:
  - Filter by company
  - Analyze spending over time
  - Export or share data
- **Reduced manual data entry** when logging bills into a spreadsheet.

## Installation and Usage

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or navigate to the BillReader directory**:
   ```bash
   cd /path/to/BillReader
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - `pdfplumber` - for extracting text from PDF bills
   - `openpyxl` - for creating and updating Excel spreadsheets

### Usage

BillReader processes PDF bill files and creates/updates a spreadsheet named `bills.xlsx` in the current directory.

#### Process a single bill file:
```bash
python billreader.py path/to/bill.pdf
```

#### Process all PDFs in a directory:
```bash
python billreader.py path/to/bills/directory
```

#### Process multiple specific files:
```bash
python billreader.py bill1.pdf bill2.pdf bill3.pdf
```

### Output

- BillReader creates (or updates) a file called `bills.xlsx` in the project root directory.
- Each company gets its own sheet/tab named `companyname_bill`.
- Each sheet contains three columns: `month`, `year`, and `amount`.
- New bills from the same company are appended as new rows to the existing sheet.

### Example

```bash
# Process all bills in the bills/ directory
python billreader.py bills/

# The script will:
# 1. Extract information from each PDF
# 2. Create or update bills.xlsx
# 3. Show progress and results for each bill processed
```

### Notes

- If a bill cannot be parsed completely, BillReader will use default values (month: 1, year: 1970) so you can easily identify and manually correct them.
- The spreadsheet format is compatible with Microsoft Excel, Google Sheets, and other spreadsheet applications.

### Possible Future Enhancements

Below are some natural extensions of the core idea (you can implement these over time):

- **Support more bill formats** (different layouts, emails, screenshots).
- **Currency and locale awareness** for amounts and dates.
- **Automatic detection of billing period vs. due date**.
- **Basic analytics** such as:
  - Monthly/annual spend per company
  - Visualizations (charts) of trends over time

---

## Configuration and Limitations

- **Spreadsheet location**: The output spreadsheet (`bills.xlsx`) is created in the current working directory where you run the script.
- **Supported formats**: Currently supports PDF bills. The parser uses heuristics to extract company names, dates, and amounts, so results may vary depending on bill format.
- **Known limitations**:
  - Bill parsing relies on text extraction from PDFs; scanned images or poorly formatted PDFs may not parse correctly.
  - Company name detection works best with known providers; unknown companies may use the first line of text as the company name.
  - Date parsing looks for common patterns but may default to placeholder values if dates aren't found in expected formats.
