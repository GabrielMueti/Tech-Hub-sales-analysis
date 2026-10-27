import csv
from pathlib import Path
import math
import re

DATA_PATH = Path("electronics_sales.csv")


def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows."""
    with path.open("r", newline="", encoding="utf-8-sig") as sales_file:
        reader = csv.DictReader(sales_file)
        columns = reader.fieldnames or []
        rows = list(reader)

    print(f"Rows read: {len(rows)}")
    print("Columns found:", ", ".join(columns))
    return rows


def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None if it cannot be trusted."""
    if value is None:
        return None

    text = value.strip()
    if not text:
        return None

    # Accept an optional KES label
    text = re.sub(r"^KES\s*", "", text, flags=re.IGNORECASE)

    # Accept commas only when they are correctly grouped as thousands separators.
    number_pattern = r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?"
    if not re.fullmatch(number_pattern, text):
        return None

    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return None

    if not math.isfinite(number):
        return None

    return number


def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return (clean_rows, skipped_rows). Clean rows have numeric quantity, unit price and revenue."""
    clean_rows = []
    skipped_rows = []

    for row in rows:
        quantity = parse_number(row.get("quantity", ""))
        unit_price = parse_number(row.get("unit_price_kes"))
        reasons = []

        if quantity is None:
            reasons.append("quantity is blank or not a valid number")
        elif quantity <= 0:
            reasons.append("quantity must be greater than zero")
        elif not quantity.is_integer():
            reasons.append("quantity must be a whole number")

        if unit_price is None:
            reasons.append("unit_price is blank or not a valid number")
        elif unit_price <= 0:
            reasons.append("unit_price must be greater than zero")

        if reasons:
            skipped_row = dict(row)
            skipped_row["skip_reason"] = "; ".join(reasons)
            skipped_rows.append(skipped_row)
            continue

        clean_row = dict(row)
        clean_row["quantity"] = int(quantity)
        clean_row["unit_price"] = unit_price
        clean_row["revenue"] = int(quantity) * unit_price
        clean_rows.append(clean_row)

    return clean_rows, skipped_rows


def total_revenue(rows: list[dict]) -> float:
    return sum(row["revenue"] for row in rows)


def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Total revenue grouped by any column (product, store, payment_method...)."""
    totals = {}

    for row in rows:
        if field not in row:
            raise KeyError(f"Column {field!r} was not found in the sales data.")

        group_name = str(row[field])
        totals[group_name] = totals.get(group_name, 0.0) + row["revenue"]

    return totals


def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest (key, value) pairs, highest first."""
    if n < 0:
        raise ValueError("n must be zero or greater.")

    # When revenue ties, sort names alphabetically.
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:n]


def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension)."""
    return [row for row in rows if row["revenue"] >= threshold]


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean() requires at least one value.")

    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("median() requires at least one value.")

    ordered_values = sorted(values)
    middle = len(ordered_values) // 2

    if len(ordered_values) % 2 == 1:
        return ordered_values[middle]

    return (ordered_values[middle - 1] + ordered_values[middle]) / 2


def minimum_maximum(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("minimum_maximum() requires at least one value.")

    smallest = values[0]
    largest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value
        if value > largest:
            largest = value

    return smallest, largest


def verify_with_pandas(path: Path, my_results: dict) -> None:
    """Recompute the headline numbers with pandas and print whether each one matches."""
    try:
        import pandas as pd
    except ImportError:
        print("Pandas is not installed. Install it with: python -m pip install pandas")
        return

    frame = pd.read_csv(
        path,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )

    required_columns = {"quantity", "product"}
    missing_columns = required_columns.difference(frame.columns)

    if "unit_price_kes" in frame.columns:
        price_column = "unit_price_kes"
    else:
        price_column = None
        missing_columns.add("unit_price_kes")

    if missing_columns:
        raise ValueError(
            "CSV is missing required column(s): "
            + ", ".join(sorted(missing_columns))
        )

    frame["quantity_number"] = frame["quantity"].map(parse_number)
    frame["price_number"] = frame[price_column].map(parse_number)

    valid_quantity = frame["quantity_number"].map(
        lambda value: (
            value is not None
            and value > 0
            and value.is_integer()
        )
    )
    valid_price = frame["price_number"].map(
        lambda value: value is not None and value > 0
    )

    frame = frame.loc[valid_quantity & valid_price].copy()
    frame["revenue"] = frame["quantity_number"] * frame["price_number"]

    pandas_total = float(frame["revenue"].sum())
    pandas_product_revenue = {
        str(product): float(revenue)
        for product, revenue in frame.groupby("product")["revenue"].sum().items()
    }
    pandas_top_products = top_n(pandas_product_revenue, 3)

    total_matches = math.isclose(
        my_results["total_revenue"],
        pandas_total,
        rel_tol=1e-9,
        abs_tol=0.01,
    )

    products_match = (
        set(my_results["product_revenue"]) == set(pandas_product_revenue)
        and all(
            math.isclose(
                my_results["product_revenue"][product],
                pandas_product_revenue[product],
                rel_tol=1e-9,
                abs_tol=0.01,
            )
            for product in my_results["product_revenue"]
        )
    )

    top_products_match = (
        len(my_results["top_products"]) == len(pandas_top_products)
        and all(
            python_item[0] == pandas_item[0]
            and math.isclose(
                python_item[1],
                pandas_item[1],
                rel_tol=1e-9,
                abs_tol=0.01,
            )
            for python_item, pandas_item
            in zip(my_results["top_products"], pandas_top_products)
        )
    )

    print(f"Total revenue: {'MATCH' if total_matches else 'MISMATCH'}")
    print(f"Product revenue: {'MATCH' if products_match else 'MISMATCH'}")
    print(f"Top three products: {'MATCH' if top_products_match else 'MISMATCH'}")

def format_money(amount: float) -> str:
    return f"KES {amount:,.2f}"


if __name__ == "__main__":
    #TODO

    #Display data
    sales = read_sales()
    clean_rows, skipped_rows = convert_rows(sales)

    #Display revenue
    transaction_revenues = [row["revenue"] for row in clean_rows]

    total = total_revenue(clean_rows)
    product_totals = revenue_by(clean_rows, "product")
    store_totals = revenue_by(clean_rows, "store")
    payment_totals = revenue_by(clean_rows, "payment_method")

    top_products = top_n(product_totals, 3)
    big_sales = high_value(clean_rows, 50_000)

    # Count the high-value sales for each store with a dictionary comprehension.
    high_value_counts = {
        store: sum(1 for row in big_sales if row["store"] == store)
        for store in sorted({row["store"] for row in clean_rows})
    }

    smallest_revenue, largest_revenue = minimum_maximum(transaction_revenues)

    report_lines = [
        "TECH HUB KENYA - SEPTEMBER SALES REPORT",
        "=" * 42,
        f"Rows read: {len(sales)}",
        f"Rows included: {len(clean_rows)}",
        f"Rows skipped: {len(skipped_rows)}",
        f"Total revenue: {format_money(total)}",
        "",
        "REVENUE BY PRODUCT (highest first)",
    ]

    for product, revenue in sorted(
        product_totals.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        report_lines.append(f"  {product}: {format_money(revenue)}")

    report_lines.extend(["", "REVENUE BY STORE"])
    for store, revenue in sorted(
        store_totals.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        report_lines.append(f"  {store}: {format_money(revenue)}")

    report_lines.extend(["", "REVENUE BY PAYMENT METHOD"])
    for method, revenue in sorted(
        payment_totals.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        report_lines.append(f"  {method}: {format_money(revenue)}")

    report_lines.extend(["", "TOP THREE PRODUCTS"])
    for rank, (product, revenue) in enumerate(top_products, start=1):
        report_lines.append(f"  {rank}. {product}: {format_money(revenue)}")

    report_lines.extend([
        "",
        "HIGH-VALUE SALES (KES 50,000 or more)",
        f"  Number of qualifying sales: {len(big_sales)}",
    ])

    for row in big_sales:
        sale_id = row.get(
            "sale_id",
            row.get("transaction_id", "(no sale ID)"),
        )
        report_lines.append(
            f"  {sale_id} | {row['store']} | {row['product']} | "
            f"{format_money(row['revenue'])}"
        )

    report_lines.append("  High-value sales by store:")
    for store, count in high_value_counts.items():
        report_lines.append(f"    {store}: {count}")

    report_lines.extend([
        "",
        "PER-TRANSACTION REVENUE STATISTICS",
        f"  Mean: {format_money(mean(transaction_revenues))}",
        f"  Median: {format_money(median(transaction_revenues))}",
        f"  Minimum: {format_money(smallest_revenue)}",
        f"  Maximum: {format_money(largest_revenue)}",
        "",
        "SKIPPED ROWS",
    ])

    if skipped_rows:
        for row in skipped_rows:
            sale_id = row.get(
                "sale_id",
                row.get("transaction_id", "(no sale ID)"),
            )
            report_lines.append(f"  {sale_id}: {row['skip_reason']}")
    else:
        report_lines.append("  None")

    ##Print and save report
    report_text = "\n".join(report_lines) + "\n"
    print("\n" + report_text)

    output_path = Path("output") / "sales_report.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Report saved to: {output_path}")

    my_results = {
        "total_revenue": total,
        "product_revenue": product_totals,
        "top_products": top_products,
    }

    print("\nPANDAS VERIFICATION")
    verify_with_pandas(DATA_PATH, my_results)
