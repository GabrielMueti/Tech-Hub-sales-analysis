Tech Hub Kenya — September Sales Analysis

## Overview

Tech Hub Kenya sells phones, laptops, and accessories across its Nairobi, Mombasa, Kisumu, and Nakuru stores. This project turns the September 2026 till export into a clear sales report: total revenue, product and store performance, high-value transactions, and a few useful statistics.

The export includes a small number of incomplete or inconsistently typed quantity and price values. The script uses Python’s standard library to read the file, apply consistent cleaning rules, and keep a reason for every skipped sale. Pandas is used separately to check the main calculations.

## Project contents

```text
day2-sales-analytics/
├── sales_analysis.py
├── electronics_sales.csv
├── output/
│   └── sales_report.txt
├── requirements.txt
└── README.md
```

The current script looks for `electronics_sales.csv` beside `sales_analysis.py`. 
```python
DATA_PATH = Path("data") / "electronics_sales.csv"
```

The dataset has columns for the sale ID, date, store, product, quantity, unit price, and payment method. 

## Getting started

Tasks 1–7 use only Python’s standard library, so they need no extra packages. Pandas is needed for Task 8, which checks the calculations on your laptop.

Install pandas from the project folder:

```bash
python -m pip install -r requirements.txt
```

Then run the analysis from the same folder:

```bash
python sales_analysis.py
```

The report appears in the terminal and is saved as `output/sales_report.txt`. The script creates the `output` folder if it does not already exist. If pandas is unavailable, the standard-library report can still be created; the verification step will print an installation message.

## How the data is cleaned

CSV values arrive as text, so the script first decides which quantity and unit price values can be read safely. It uses the same rules for both fields:

- Leading and trailing spaces are removed. Blank or missing values are treated as invalid.
- An optional `KES` prefix is accepted at the beginning of a value, regardless of capitalization.
- Commas are accepted only as correctly grouped thousands separators. For example, `1,200` and `1,200.50` are accepted; `1,20` is not.
- After removing an optional prefix and valid commas, the whole value must be a number with an optional sign and decimal part. The script does not guess how to repair other text or malformed numbers.
- Quantity must be a positive whole number. Blank, malformed, zero, negative, and fractional quantities cause the sale to be skipped.
- Unit price must be greater than zero. Blank, malformed, zero, and negative prices cause the sale to be skipped.
- A sale is included only when both quantity and price pass these checks. Revenue is calculated as quantity multiplied by unit price.
- Every skipped sale is kept with a reason. Skipped sales do not contribute to revenue totals, rankings, high-value counts, or transaction statistics.

This approach keeps the calculations reproducible: values that fit the stated rules are used, and values that do not are visible in the report instead of being silently guessed.

## What the report calculates

- **Total revenue:** the sum of revenue for all included sales, formatted in KES with two decimal places.
- **Revenue by product, store, and payment method:** grouped with ordinary Python dictionaries.
- **Top three products:** ranked by revenue, highest first. Alphabetical product name breaks a revenue tie.
- **High-value sales:** transactions with revenue of KES 50,000 or more, plus the count for each store.
- **Transaction statistics:** mean, median, minimum, and maximum revenue across included sales.

The supplied file is treated as the September dataset; the script does not filter by date. Revenue is quantity multiplied by listed unit price. The analysis does not add tax, discounts, or other adjustments. If a statistical function receives no values, it raises a clear `ValueError` rather than returning a misleading result.

## Checking the calculations with pandas

The pandas step applies the same number parser and validity rules as the standard-library analysis. It recalculates total revenue, revenue by product, and the top three products, then prints `MATCH` or `MISMATCH` for each comparison. This helps confirm that the hand-written aggregation gives the same result as a second approach.



## Current results

The standard-library run read 50 sales, included 46, and skipped 4. It calculated total revenue of **KES 1,310,812.00**. The pandas comparison still needs to be rerun with the corrected price-column handling, so verification is not yet marked complete.
