import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple


def dedupe(items: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for item in items:
        key = (item.get("text"), item.get("author"))
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def dedupe_by(items: List[Dict], key: str) -> List[Dict]:
    """Giữ bản ghi đầu tiên cho mỗi giá trị của khóa (thường là url)."""
    seen, out = set(), []
    for item in items:
        value = item.get(key)
        if value not in seen:
            seen.add(value)
            out.append(item)
    return out


def save(items: List[Dict], out_dir: Path, name: str) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{name}.json"
    csv_path = out_dir / f"{name}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # utf-8-sig để Excel mở tiếng Việt không bị lỗi font
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "author", "tags"])
        for it in items:
            writer.writerow([it["text"], it["author"], "|".join(it["tags"])])

    return json_path, csv_path


PRODUCT_COLUMNS = [
    "source",
    "name",
    "condition",
    "price_vnd",
    "price_text",
    "old_price_vnd",
    "stock",
    "in_stock",
    "description",
    "images",
    "url",
    "crawled_at",
]


def save_products(items: List[Dict], out_dir: Path, name: str) -> Tuple[Path, Path]:
    """Ghi JSON (giữ nguyên list ảnh) + CSV (nối ảnh bằng dấu |)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{name}.json"
    csv_path = out_dir / f"{name}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_COLUMNS)
        writer.writeheader()
        for item in items:
            row = {k: item.get(k, "") for k in PRODUCT_COLUMNS}
            row["images"] = "|".join(item.get("images") or [])
            writer.writerow(row)

    return json_path, csv_path
