"""Read-only recipe preflight; writes reports only to --output-dir."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

NUTRIENTS = ("energy", "carb", "protein", "fat", "vitaminC", "fiber", "sodium")


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def check(source: Path):
    findings, records = [], []
    identities = defaultdict(list)

    def flag(level, code, file, detail):
        findings.append(dict(level=level, code=code, file=file, detail=detail))

    for path in sorted(source.glob("*.json")):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        try:
            recipe = json.loads(raw.decode("utf-8-sig"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            if not isinstance(recipe, dict):
                raise ValueError("root must be an object")
        except (ValueError, UnicodeError) as exc:
            flag("error", "invalid_json", path.name, str(exc))
            continue
        rid = recipe.get("id")
        if not isinstance(rid, str) or not rid.strip():
            flag("error", "missing_id", path.name, "stable id required")
        else:
            identities[rid].append(dict(file=path.name, sha256=digest))
        items = recipe.get("items")
        if not isinstance(items, list) or not items:
            flag("error", "invalid_items", path.name, "nonempty items array required")
            continue
        record = dict(file=path.name, id=rid, name=recipe.get("name"), sha256=digest,
                      schemaVersion=recipe.get("schemaVersion"), itemCount=len(items),
                      missingFoodState=0, missingItemId=0, missingWeightBounds=0,
                      totalsCheck={}, missingDisplayFields=[])
        if recipe.get("schemaVersion") != 2:
            flag("warning", "schema_migration", path.name, recipe.get("schemaVersion"))
        for name in ("dishType", "tags", "summary", "image", "revision", "includesStaple"):
            if name not in recipe:
                record["missingDisplayFields"].append(name)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                flag("error", "invalid_item", path.name, dict(index=index))
                continue
            name = item.get("name", str(index))
            weight = item.get("weight")
            if not valid_number(weight) or weight == 0:
                flag("error", "invalid_weight", path.name, dict(item=name, value=weight))
            hw = item.get("healthWeight")
            if not valid_number(hw) or not 0.01 <= hw <= 1 or abs(hw * 100 - round(hw * 100)) > 1e-7:
                flag("error", "invalid_health_weight", path.name, dict(item=name, value=hw))
            if "locked" in item and not isinstance(item["locked"], bool):
                flag("error", "invalid_locked", path.name, dict(item=name))
            record["missingFoodState"] += not bool(item.get("foodState"))
            record["missingItemId"] += not bool(item.get("itemId"))
            record["missingWeightBounds"] += "minWeight" not in item or "maxWeight" not in item
            per100 = item.get("per100")
            for nutrient in NUTRIENTS:
                amount = item.get(nutrient)
                reference = per100.get(nutrient) if isinstance(per100, dict) else None
                if not valid_number(amount) or not valid_number(reference):
                    flag("warning", "unknown_nutrient", path.name, dict(item=name, nutrient=nutrient))
                elif valid_number(weight):
                    expected = reference * weight / 100
                    # Existing values are often rounded to one decimal place.
                    if abs(expected - amount) > 0.15:
                        flag("error", "per100_mismatch", path.name,
                             dict(item=name, nutrient=nutrient, declared=amount, calculated=round(expected, 4)))
            if not item.get("source") and not item.get("sourceRef"):
                flag("warning", "missing_nutrition_source", path.name, dict(item=name))
        totals = recipe.get("totals")
        if not isinstance(totals, dict):
            flag("error", "missing_totals", path.name, "totals object required")
            totals = {}
        for key in ("weight", *NUTRIENTS):
            amounts = [item.get(key) if isinstance(item, dict) else None for item in items]
            declared = totals.get(key)
            if valid_number(declared) and all(valid_number(value) for value in amounts):
                actual = sum(amounts)
                delta = declared - actual
                record["totalsCheck"][key] = dict(declared=declared, summed=round(actual, 4), delta=round(delta, 4))
                if abs(delta) > max(0.11, 0.05 * len(items) + 0.01):
                    flag("error", "totals_mismatch", path.name, dict(field=key, delta=round(delta, 4)))
            else:
                flag("warning", "unknown_total", path.name, dict(field=key))
        source_names = {entry.get("name") for entry in recipe.get("sources", []) if isinstance(entry, dict)}
        if not source_names:
            flag("warning", "missing_source_list", path.name, "no named sources")
        if record["missingFoodState"]:
            flag("warning", "food_state_unverified", path.name, dict(count=record["missingFoodState"]))
        if record["missingDisplayFields"]:
            flag("warning", "new_fields_missing", path.name, record["missingDisplayFields"])
        records.append(record)
    duplicate_ids = []
    for rid, files in identities.items():
        if len(files) > 1:
            identical = len({entry["sha256"] for entry in files}) == 1
            duplicate_ids.append(dict(id=rid, identical=identical, files=files))
            # Definition IDs and file hashes are audit facts, not library identity.
            # Keep every record, including byte-identical files.
            flag("warning", "duplicate_id", ", ".join(entry["file"] for entry in files),
                 dict(id=rid, identical=identical, action="audit_only_keep_independent"))
    if not records:
        flag("error", "no_recipes", str(source), "no readable recipe records")
    return dict(source=str(source), filesFound=len(list(source.glob("*.json"))),
                filesParsed=len(records), uniqueIds=len(identities),
                errorCount=sum(f["level"] == "error" for f in findings),
                warningCount=sum(f["level"] == "warning" for f in findings),
                duplicateIds=duplicate_ids, records=records, findings=findings,
                limits=["Structural and arithmetic checks only; nutrition provenance, licensing, food state and naming require review.",
                        "Original files are read only; no migration or automatic correction performed.",
                        "Every source file remains independent; equal names, definition IDs or hashes never authorize deduplication. uniqueIds counts definition IDs only."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = check(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "recipe-audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("filesFound", "filesParsed", "uniqueIds", "errorCount", "warningCount")}, ensure_ascii=False))
    print(f"report: {output}")
    return 2 if report["errorCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
