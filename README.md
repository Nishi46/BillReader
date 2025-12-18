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

### Possible Future Enhancements

Below are some natural extensions of the core idea (you can implement these over time):

- **Support more bill formats** (different layouts, emails, screenshots).
- **Currency and locale awareness** for amounts and dates.
- **Automatic detection of billing period vs. due date**.
- **Integration with Google Sheets or Excel online** for live syncing.
- **Basic analytics** such as:
  - Monthly/annual spend per company
  - Visualizations (charts) of trends over time

---

This README describes the **intended behavior and data model** of BillReader.  
As the implementation evolves, you can expand this file with:
- **Installation instructions**
- **Usage examples**
- **Configuration details** (e.g. API keys, storage locations)
- **Limitations and known issues**

