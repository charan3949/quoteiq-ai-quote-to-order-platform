from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


def _load_csv(filename: str):
    path = DATA_DIR / filename
    df = pd.read_csv(path)
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")


def load_product_catalog():
    return _load_csv("product_catalog.csv")


def load_customers():
    return _load_csv("customers.csv")


def load_price_rules():
    return _load_csv("price_rules.csv")


def load_margin_policies():
    return _load_csv("margin_policies.csv")