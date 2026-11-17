"""
ETL: mağaza satış və plan fayllarını oxuyur, təmizləyir və data/processed/ qovluğuna 3 CSV yazır.

    fact_sales.csv   Mağaza_Kodu, Tarix, Satış
    fact_plan.csv    Mağaza_Kodu, Tarix, Plan
    dim_store.csv    mağaza atributları (region, açılış ili, status, ölçü qrupu)

İstifadə:
    python src/etl.py --raw "yol/Mağaza Satış.xlsx" "yol/Mağaza Planı.xlsx"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
SALES_SHEET, PLAN_SHEET = "Mağaza Satış 2", "Mağaza Plan"   # digər vərəqlər ("Sheet4") iş hesablamalarıdır
LAST_ACTIVE_FROM = pd.Timestamp("2025-09-01")              # bu tarixdən sonra satışı olan mağaza "Aktiv" sayılır


def load(path: Path, sheet: str, value: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet)
    df = df.rename(columns={"Mağaza Kodu": "Mağaza_Kodu", "Mağaza adı": "Mağaza_adı"})
    df["Tarix"] = pd.to_datetime(df["Tarix"]).dt.normalize()
    df[value] = pd.to_numeric(df[value], errors="coerce").round(4)
    df["Mağaza_Kodu"] = df["Mağaza_Kodu"].astype(str).str.strip()
    df["Mağaza_adı"] = df["Mağaza_adı"].astype(str).str.strip()
    return df.dropna(subset=["Tarix", value, "Mağaza_Kodu"])


def build_dim(sales: pd.DataFrame, plan: pd.DataFrame) -> pd.DataFrame:
    names = pd.concat([sales[["Mağaza_Kodu", "Mağaza_adı"]], plan[["Mağaza_Kodu", "Mağaza_adı"]]]).drop_duplicates("Mağaza_Kodu")
    dim = names.copy()
    dim["Region"] = dim["Mağaza_adı"].str.replace(r"\s*\d+\s*$", "", regex=True).str.strip()
    dim["Mağaza_nömrəsi"] = pd.to_numeric(dim["Mağaza_adı"].str.extract(r"(\d+)\s*$")[0], errors="coerce").astype("Int64")

    life = sales.groupby("Mağaza_Kodu")["Tarix"].agg(İlk_satış="min", Son_satış="max", Satış_günü="nunique").reset_index()
    avg = sales.groupby("Mağaza_Kodu")["Satış"].mean().rename("Orta_günlük_satış").reset_index()
    dim = dim.merge(life, on="Mağaza_Kodu", how="left").merge(avg, on="Mağaza_Kodu", how="left")
    dim["Açılış_ili"] = dim["İlk_satış"].dt.year
    dim["Status"] = (dim["Son_satış"] >= LAST_ACTIVE_FROM).map({True: "Aktiv", False: "Bağlanıb"})

    # ABC tipli ölçü qrupu: orta günlük satışa görə üçdə bir
    q1, q2 = dim["Orta_günlük_satış"].quantile([1 / 3, 2 / 3])
    dim["Ölçü_qrupu"] = pd.cut(dim["Orta_günlük_satış"], [-1, q1, q2, 1e12], labels=["Kiçik", "Orta", "Böyük"]).astype(str)
    big_city = {"Bakı", "Abşeron", "Sumqayıt", "Xırdalan"}
    dim["Region_qrupu"] = dim["Region"].map(lambda r: "Bakı və Abşeron" if r in big_city else "Rayonlar")
    return dim.drop(columns=["Mağaza_adı"]).merge(names[["Mağaza_Kodu", "Mağaza_adı"]], on="Mağaza_Kodu")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", nargs=2, required=True, metavar=("SATIŞ_XLSX", "PLAN_XLSX"))
    a = ap.parse_args()

    sales = load(Path(a.raw[0]), SALES_SHEET, "Satış")
    plan = load(Path(a.raw[1]), PLAN_SHEET, "Plan")
    dim = build_dim(sales, plan)

    OUT.mkdir(parents=True, exist_ok=True)
    sales[["Mağaza_Kodu", "Tarix", "Satış"]].sort_values(["Tarix", "Mağaza_Kodu"]).to_csv(OUT / "fact_sales.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d")
    plan[["Mağaza_Kodu", "Tarix", "Plan"]].sort_values(["Tarix", "Mağaza_Kodu"]).to_csv(OUT / "fact_plan.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d")
    cols = ["Mağaza_Kodu", "Mağaza_adı", "Region", "Region_qrupu", "Mağaza_nömrəsi", "Açılış_ili", "İlk_satış", "Son_satış", "Satış_günü", "Orta_günlük_satış", "Ölçü_qrupu", "Status"]
    dim[cols].sort_values(["Region", "Mağaza_nömrəsi"]).to_csv(OUT / "dim_store.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d", float_format="%.2f")

    print(f"fact_sales {len(sales):>8,} sətir | fact_plan {len(plan):>8,} sətir | dim_store {len(dim):>4} mağaza | {dim['Region'].nunique()} region")
    chk = [
        ("mağaza kodu = ad (1:1)", sales.groupby("Mağaza_Kodu")["Mağaza_adı"].nunique().max() == 1),
        ("satış: dublikat mağaza-gün yoxdur", not sales.duplicated(["Mağaza_Kodu", "Tarix"]).any()),
        ("plan: dublikat mağaza-gün yoxdur", not plan.duplicated(["Mağaza_Kodu", "Tarix"]).any()),
        ("satışda mənfi/sıfır dəyər yoxdur", bool((sales["Satış"] > 0).all())),
        ("plandakı hər mağaza satışda var", set(plan["Mağaza_Kodu"]) <= set(sales["Mağaza_Kodu"])),
    ]
    for name, ok in chk:
        print(("OK   " if ok else "XƏTA ") + name)


if __name__ == "__main__":
    main()
