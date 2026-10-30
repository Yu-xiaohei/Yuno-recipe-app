"""B01 structural regressions. This does not implement the B03 domain validator."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_BASE = "https://yuno-recipe.invalid/schemas/"


def reject_constant(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text):
    return json.loads(
        text,
        parse_float=Decimal,
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def read_json(path):
    return parse_json(path.read_text(encoding="utf-8-sig"))


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = FormatChecker()
        required_formats = {"date", "date-time", "uri"}
        missing = required_formats.difference(cls.checker.checkers)
        if missing:
            raise RuntimeError(
                f"Missing required format checks: {sorted(missing)}. "
                "Install tests/test_contract_deps/requirements.txt in the project .venv."
            )
        cls.schemas = {
            path.name: read_json(path)
            for path in sorted((ROOT / "schemas").glob("*.schema.json"))
        }
        cls.registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema))
            for schema in cls.schemas.values()
        )
        cls.samples = read_json(ROOT / "tests/test_contract_samples.json")

    def validator(self, name, fragment=None):
        schema = self.schemas[f"{name}.schema.json"]
        if fragment:
            schema = {"$ref": schema["$id"] + fragment}
        return Draft202012Validator(
            schema, registry=self.registry, format_checker=self.checker
        )

    def assert_valid(self, name, value, fragment=None):
        errors = list(self.validator(name, fragment).iter_errors(value))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def assert_invalid(self, name, value, fragment=None):
        self.assertFalse(self.validator(name, fragment).is_valid(value))

    def entry(self, kind="ingredient", weight=100):
        snapshot = copy.deepcopy(self.samples[kind])
        nutrient_values = snapshot.get("per100", snapshot.get("totals"))
        totals = {
            key: value
            for key, value in nutrient_values.items()
            if key != "weight"
        }
        totals["weight"] = weight
        return {
            "entryId": "test_entry",
            "originNamespace": "test_library",
            "libraryEntryId": f"test_library_{kind}",
            "sourceKind": kind,
            "sourceId": snapshot["id"],
            "sourceRevision": snapshot["revision"],
            "sourceContentHash": "a" * 64,
            "portionBasisHash": "b" * 64,
            "originalPortionWeight": 100,
            "sourceCount": 1,
            "requestedWeight": weight,
            "actualWeight": weight,
            "originalSnapshot": snapshot,
            "adjustedItems": [
                {
                    "itemId": "test_item" if kind == "recipe" else snapshot["id"],
                    "weight": weight,
                }
            ],
            "totals": totals,
            "adjustment": {
                "mode": "weight",
                "requestedTarget": weight,
                "actualTarget": weight,
                "reachableMin": 0,
                "reachableMax": 200,
                "status": "exact",
                "actualValueAccepted": False,
                "warnings": [],
            },
        }

    def meal(self, kind="ingredient", weight=100):
        entry = self.entry(kind, weight)
        return {
            "schemaVersion": 1,
            "kind": "mealRecord",
            "id": "test_meal",
            "revision": "test_rev1",
            "parentRevision": None,
            "deviceId": "test_device",
            "date": "2026-10-28",
            "mealSlotSnapshot": {"id": "test_lunch", "name": "TEST", "order": 1},
            "goalSnapshot": None,
            "entries": [entry],
            "totals": copy.deepcopy(entry["totals"]),
            "calculationVersion": "bounded-healthweight-v1",
            "isLocked": False,
            "syncEnabled": False,
            "createdAt": "2026-10-28T12:00:00+08:00",
            "updatedAt": "2026-10-28T12:00:00+08:00",
            "deletedAt": None,
        }

    def tombstone(self, index=0):
        return {
            "schemaVersion": 1,
            "kind": "mealTombstone",
            "id": f"test_meal_{index}",
            "revision": "test_deleted",
            "parentRevision": "test_rev1",
            "deviceId": "test_device",
            "date": "2026-10-28",
            "mealSlotId": "test_lunch",
            "deletedAt": "2026-10-28T13:00:00Z",
        }

    def goal_profile(self):
        return {
            "schemaVersion": 1,
            "kind": "goalProfile",
            "id": "test_goals",
            "revision": "test_r1",
            "updatedAt": "2026-10-28T12:00:00Z",
            "rulesVersion": "goal-status-v1",
            "dailyGoals": {},
            "mealSlots": [],
        }

    def test_all_schema_documents_and_refs_resolve_offline(self):
        self.assertEqual(8, len(self.schemas))
        for schema in self.schemas.values():
            with self.subTest(schema=schema["$id"]):
                Draft202012Validator.check_schema(schema)
                for node in nodes(schema):
                    if "$ref" in node:
                        self.registry.resolver(schema["$id"]).lookup(node["$ref"])
        with self.assertRaises(Unresolvable):
            self.registry.resolver().lookup("https://missing.invalid/unregistered")

    def test_required_formats_are_active(self):
        self.assertFalse(self.checker.conforms("2026-02-30T12:00:00Z", "date-time"))
        self.assertFalse(self.checker.conforms("2026-02-30", "date"))
        self.assertFalse(self.checker.conforms("not a uri", "uri"))

    def test_synthetic_sources_accept_null_and_half_serving(self):
        for kind in ("recipe", "ingredient"):
            self.assert_valid(kind, self.samples[kind])
        self.assertIsNone(self.samples["ingredient"]["per100"]["energy"])
        self.assertEqual(Decimal("0.5"), self.samples["recipe"]["serving"])

    def test_legacy_reference_files_are_recognized_but_not_canonical(self):
        originals = sorted((ROOT / "data/reference/recipes").glob("*.json"))
        self.assertEqual(13, len(originals))
        for path in originals:
            with self.subTest(path=path.name):
                source = read_json(path)
                self.assert_valid("recipe", source)
                self.assert_valid("recipe", source, "#/$defs/legacy")
                self.assert_invalid("recipe", source, "#/$defs/canonical")

    def test_decimal_health_weights_have_no_binary_float_false_failure(self):
        for value in ("0.01", "0.07", "0.14", "0.29", "0.57", "0.58", "1.00"):
            with self.subTest(value=value):
                self.assert_valid("common", Decimal(value), "#/$defs/healthWeight")
        for value in ("0", "0.001", "0.071", "1.01"):
            self.assert_invalid("common", Decimal(value), "#/$defs/healthWeight")

    def test_nutrients_require_explicit_fields_and_reject_negatives(self):
        for bad in (-1, "0", False):
            ingredient = copy.deepcopy(self.samples["ingredient"])
            ingredient["per100"]["energy"] = bad
            self.assert_invalid("ingredient", ingredient)
        ingredient = copy.deepcopy(self.samples["ingredient"])
        del ingredient["per100"]["energy"]
        self.assert_invalid("ingredient", ingredient)

    def test_kind_and_versions_cannot_be_guessed(self):
        for key, bad in (("schemaVersion", 99), ("kind", "recipe"), ("profile", "unknown")):
            ingredient = copy.deepcopy(self.samples["ingredient"])
            ingredient[key] = bad
            self.assert_invalid("ingredient", ingredient)

    def test_paths_reject_traversal_absolute_encoded_and_controls(self):
        for path in ("recipes/a.json", "images/a-b_1.png"):
            self.assert_valid("common", path, "#/$defs/safeRelativePath")
        for path in (
            "../a", "a/../b", "a/./b", "/a", "C:/a", "https://example.invalid/a",
            "a\\b", "a/%2e%2e/b", "a?token=x", "a#b", "a/b.json\n", "a/\x00b",
        ):
            with self.subTest(path=repr(path)):
                self.assert_invalid("common", path, "#/$defs/safeRelativePath")

    def test_identity_hash_date_and_uri_reject_invalid_values(self):
        for fragment, value in (
            ("id", "abc\n"),
            ("contentHash", "a" * 64 + "\n"),
            ("localDate", "2026-10-28\n"),
            ("dateTime", "2026-10-28T12:00:00Z\n"),
            ("dateTime", "2026-10-28T12:00:00"),
            ("localDate", "2026-02-30"),
        ):
            self.assert_invalid("common", value, f"#/$defs/{fragment}")
        ingredient = copy.deepcopy(self.samples["ingredient"])
        ingredient["sourceRef"]["url"] = "not a uri"
        self.assert_invalid("ingredient", ingredient)

    def test_verified_source_requires_evidence_locator(self):
        source = copy.deepcopy(self.samples["ingredient"]["sourceRef"])
        source["verification"] = "verified"
        source["title"] = "TEST evidence"
        self.assert_invalid("common", source, "#/$defs/sourceRef")
        source["locator"] = "TEST page 1"
        self.assert_valid("common", source, "#/$defs/sourceRef")

    def test_ingredient_nutrition_basis_is_separate_from_initial_portion(self):
        for field in ("nutritionBasisWeight", "defaultPortionWeight"):
            ingredient = copy.deepcopy(self.samples["ingredient"])
            ingredient[field] = 99
            self.assert_invalid("ingredient", ingredient)

    def test_goal_modes_zero_upper_and_units(self):
        for goals in (
            {},
            {"sodium": {"mode": "max", "unit": "mg", "upper": 0}},
            {"energy": {"mode": "target", "unit": "kcal", "target": 100}},
            {"weight": {"mode": "range", "unit": "g", "lower": 0, "upper": 10}},
        ):
            self.assert_valid("goal", goals, "#/$defs/goalMap")
        for goals in (
            {"energy": {"mode": "target", "unit": "kcal", "target": 0}},
            {"energy": {"mode": "range", "unit": "kcal", "lower": 0, "upper": 0}},
            {"sodium": {"mode": "max", "unit": "g", "upper": 0}},
            {"energy": {"mode": "max", "unit": "kcal", "upper": 100, "target": 20}},
            {"energy": None},
            {"unknown": {"mode": "max", "unit": "g", "upper": 1}},
        ):
            self.assert_invalid("goal", goals, "#/$defs/goalMap")
        self.assert_valid("goal", self.goal_profile())

    def test_saved_recipe_and_ingredient_snapshot_records(self):
        for kind in ("recipe", "ingredient"):
            self.assert_valid("meal", self.meal(kind))
        unsupported_mode = self.meal()
        unsupported_mode["entries"][0]["adjustment"]["mode"] = "energy"
        self.assert_invalid("meal", unsupported_mode)
        meal = self.meal()
        profile = self.goal_profile()
        meal["goalSnapshot"] = {
            "profileId": profile["id"],
            "profileRevision": profile["revision"],
            "rulesVersion": profile["rulesVersion"],
            "goals": profile["dailyGoals"],
        }
        self.assert_valid("meal", meal)

    def test_subgram_drafts_survive_but_saved_records_are_rejected(self):
        for weight in (0, Decimal("0.1"), Decimal("0.9"), Decimal("0.999")):
            meal = self.meal(weight=weight)
            entry = meal["entries"][0]
            for key in ("actualWeight", "adjustedItems", "totals", "adjustment"):
                del entry[key]
            draft = {
                "schemaVersion": 1,
                "kind": "mealDraft",
                "draftId": "test_draft",
                "sourceMealId": None,
                "expectedRevision": None,
                "date": meal["date"],
                "mealSlotId": "test_lunch",
                "entries": [entry],
            }
            with self.subTest(weight=weight):
                self.assert_valid("meal", draft, "#/$defs/draft")
                self.assert_invalid("meal", draft)
                self.assert_invalid("meal", self.meal(weight=weight))
        for weight in (1, 9, 10):
            self.assert_valid("meal", self.meal(weight=weight))

    def test_valid_entry_does_not_hide_an_invalid_one(self):
        meal = self.meal()
        invalid_entry = self.entry(weight=Decimal("0.9"))
        invalid_entry["entryId"] = "test_invalid"
        meal["entries"].append(invalid_entry)
        self.assert_invalid("meal", meal)

    def test_withdrawn_source_evidence_survives_drafts_backup_and_sync(self):
        evidence = {
            "status": "withdrawn",
            "catalogRevision": "test_catalog_2",
            "deletionRevision": "test_delete_2",
            "deletedAt": "2026-10-30T01:00:00Z",
            "observedAt": "2026-10-30T02:00:00Z",
        }
        for kind in ("recipe", "ingredient"):
            with self.subTest(kind=kind):
                meal = self.meal(kind)
                meal["entries"][0]["sourceAvailability"] = copy.deepcopy(evidence)
                self.assert_valid("meal", meal)
                self.assertIsNone(meal["deletedAt"])
                self.assert_valid(
                    "sync",
                    {"schemaVersion": 1, "kind": "syncEnvelope", "payload": meal},
                )
                self.assert_valid(
                    "transfer",
                    {
                        "schemaVersion": 1,
                        "kind": "mealBackup",
                        "exportedAt": "2026-10-30T03:00:00Z",
                        "records": [meal],
                    },
                    "#/$defs/validatedMealBackup",
                )
                draft = {
                    "schemaVersion": 1,
                    "kind": "mealDraft",
                    "draftId": "test_draft",
                    "sourceMealId": meal["id"],
                    "expectedRevision": meal["revision"],
                    "date": meal["date"],
                    "mealSlotId": "test_lunch",
                    "entries": copy.deepcopy(meal["entries"]),
                }
                draft["entries"][0]["requestedWeight"] = 0
                self.assert_valid("meal", draft, "#/$defs/draft")
                for missing in evidence:
                    bad = copy.deepcopy(meal)
                    del bad["entries"][0]["sourceAvailability"][missing]
                    self.assert_invalid("meal", bad)
                for field, value in (
                    ("status", "available"),
                    ("observedAt", "not-a-date"),
                    ("catalogRevision", ""),
                    ("password", "TEST"),
                ):
                    bad = copy.deepcopy(meal)
                    bad["entries"][0]["sourceAvailability"][field] = value
                    self.assert_invalid("meal", bad)

    def test_counts_cannot_be_zero_negative_or_fractional(self):
        for count in (0, -1, Decimal("1.5")):
            meal = self.meal()
            meal["entries"][0]["sourceCount"] = count
            self.assert_invalid("meal", meal)
        meal = self.meal()
        meal["entries"][0]["originalPortionWeight"] = 0
        self.assert_invalid("meal", meal)

    def test_approximate_and_unreachable_require_explicit_actual_acceptance(self):
        for status in ("approximate", "unreachable"):
            meal = self.meal()
            adjustment = meal["entries"][0]["adjustment"]
            adjustment["status"] = status
            self.assert_invalid("meal", meal)
            adjustment["actualValueAccepted"] = True
            self.assert_valid("meal", meal)

    def test_tombstone_and_sync_exclude_settings_and_global_goals(self):
        tombstone = self.tombstone()
        self.assert_valid("meal", tombstone)
        for payload in (self.meal(), tombstone):
            self.assert_valid(
                "sync", {"schemaVersion": 1, "kind": "syncEnvelope", "payload": payload}
            )
        envelope = {"schemaVersion": 1, "kind": "syncEnvelope", "payload": self.goal_profile()}
        self.assert_invalid("sync", envelope)
        envelope["payload"] = self.meal()
        envelope["serverSettings"] = {"url": "https://example.invalid"}
        self.assert_invalid("sync", envelope)

    def test_partial_import_keeps_errors_but_strict_export_rejects_them(self):
        records = [self.tombstone(index) for index in range(8)] + [
            {"schemaVersion": 99, "kind": "mealRecord"},
            {"schemaVersion": 1, "kind": "mealDraft"},
        ]
        envelope = {
            "schemaVersion": 1,
            "kind": "mealBackup",
            "exportedAt": "2026-10-28T12:00:00Z",
            "records": records,
        }
        self.assert_valid("transfer", envelope)
        selected = [item for item in records if self.validator("meal").is_valid(item)]
        rejected = [item for item in records if not self.validator("meal").is_valid(item)]
        self.assertEqual((8, 2), (len(selected), len(rejected)))
        self.assert_invalid("transfer", envelope, "#/$defs/validatedMealBackup")
        envelope["records"] = selected
        self.assert_valid("transfer", envelope, "#/$defs/validatedMealBackup")
        # This is structural selection only; no importer or transaction is exercised.

    def test_import_envelope_versions_limits_and_credentials(self):
        envelope = {"schemaVersion": 1, "kind": "libraryImport", "records": [None, 7]}
        self.assert_valid("transfer", envelope)
        for field, value in (("schemaVersion", 2), ("password", "TEST"), ("records", [None] * 10001)):
            bad = copy.deepcopy(envelope)
            bad[field] = value
            self.assert_invalid("transfer", bad)
        meal = self.meal()
        meal["entries"][0]["originalSnapshot"]["accessKey"] = "TEST"
        self.assert_invalid("meal", meal)

    def test_mixed_catalog_has_explicit_kind_and_deletion(self):
        catalog = {
            "schemaVersion": 1,
            "kind": "catalog",
            "revision": "test_c1",
            "generatedAt": "2026-10-28T12:00:00Z",
            "entries": [
                {
                    "operation": "delete",
                    "libraryEntryId": "test_library_old",
                    "kind": "ingredient",
                    "id": "test_old",
                    "revision": "test_deleted",
                    "deletedAt": "2026-10-28T12:00:00Z",
                }
            ],
        }
        self.assert_valid("catalog", catalog)
        del catalog["entries"][0]["kind"]
        self.assert_invalid("catalog", catalog)

    def test_identical_file_hashes_allow_independent_catalog_records(self):
        raw = json.dumps(
            json.loads((ROOT / "tests/test_contract_samples.json").read_text("utf-8"))["recipe"],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        catalog = {
            "schemaVersion": 1,
            "kind": "catalog",
            "revision": "test_c1",
            "generatedAt": "2026-10-29T12:00:00Z",
            "entries": [
                {
                    "operation": "upsert",
                    "libraryEntryId": f"test_library_{index}",
                    "kind": "recipe",
                    "id": self.samples["recipe"]["id"],
                    "revision": self.samples["recipe"]["revision"],
                    "path": f"recipes/test_{index}.json",
                    "contentHash": digest,
                    "summary": {
                        "name": "TEST recipe",
                        "weight": 100,
                        "energy": None,
                        "dishType": "test",
                        "tags": ["test"],
                        "image": None,
                        "includesStaple": "unknown",
                        "publishedAt": "2026-10-29T12:00:00Z",
                    },
                }
                for index in (1, 2)
            ],
        }
        self.assert_valid("catalog", catalog)
        self.assertEqual(catalog["entries"][0]["contentHash"], catalog["entries"][1]["contentHash"])
        self.assertNotEqual(catalog["entries"][0]["libraryEntryId"], catalog["entries"][1]["libraryEntryId"])
        del catalog["entries"][1]["libraryEntryId"]
        self.assert_invalid("catalog", catalog)
        # Structural permission only: no production catalog loader or deduplicator runs.

    def test_identical_definitions_keep_distinct_meal_source_identities(self):
        meal = self.meal(kind="recipe")
        second = copy.deepcopy(meal["entries"][0])
        second["entryId"] = "test_second_entry"
        second["libraryEntryId"] = "test_second_library_record"
        meal["entries"].append(second)
        meal["totals"]["weight"] = 200
        self.assert_valid("meal", meal)
        self.assertEqual(1, meal["entries"][0]["sourceCount"])
        self.assertEqual(1, meal["entries"][1]["sourceCount"])
        for field in ("originNamespace", "libraryEntryId"):
            bad = copy.deepcopy(meal)
            del bad["entries"][1][field]
            self.assert_invalid("meal", bad)
        # The xN aggregation and source update algorithms are B03 implementation work.

    def test_preflight_shared_definition_ids_only_audit_and_keep_files(self):
        spec = importlib.util.spec_from_file_location(
            "test_preflight_module", ROOT / "scripts/check_recipe_preflight.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        recipe = json.loads((ROOT / "tests/test_contract_samples.json").read_text("utf-8"))["recipe"]
        for identical in (True, False):
            other = copy.deepcopy(recipe)
            if not identical:
                other["summary"] = "TEST changed bytes with same name and definition ID"
            raw_files = [
                json.dumps(item, ensure_ascii=False).encode("utf-8")
                for item in (recipe, other)
            ]
            files = [Path("test_source") / f"test_source_{index}.json" for index in range(2)]
            raw_by_path = dict(zip(files, raw_files))
            with self.subTest(identical=identical):
                with patch.object(Path, "glob", return_value=files), patch.object(
                    Path, "read_bytes", autospec=True, side_effect=lambda path: raw_by_path[path]
                ):
                    report = module.check(Path("test_source"))
                self.assertEqual(2, report["filesFound"])
                self.assertEqual(2, report["filesParsed"])
                self.assertEqual(2, len(report["records"]))
                self.assertEqual(1, report["uniqueIds"])  # Definition ID count only.
                self.assertEqual(0, report["errorCount"])
                self.assertEqual(identical, report["duplicateIds"][0]["identical"])
                for raw, record in zip(raw_files, report["records"]):
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                audit = next(item for item in report["findings"] if item["code"] == "duplicate_id")
                self.assertEqual("warning", audit["level"])
                self.assertEqual("audit_only_keep_independent", audit["detail"]["action"])
        # No temporary files, writes or actual imports are performed.

    def test_saved_weight_fields_enforce_one_gram_individually(self):
        paths = (
            ("entries", 0, "requestedWeight"),
            ("entries", 0, "actualWeight"),
            ("entries", 0, "totals", "weight"),
            ("entries", 0, "adjustment", "requestedTarget"),
            ("entries", 0, "adjustment", "actualTarget"),
            ("totals", "weight"),
        )
        for path in paths:
            for weight in (Decimal("0.999"), 1):
                meal = self.meal()
                parent = meal
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = weight
                with self.subTest(path=path, weight=weight):
                    if weight < 1:
                        self.assert_invalid("meal", meal)
                    else:
                        self.assert_valid("meal", meal)

    def test_parser_rejects_nonfinite_and_duplicate_keys(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":-Infinity}'):
            with self.assertRaises(ValueError):
                parse_json(text)

    def test_plan_dependencies_and_accepted_batch_evidence(self):
        plan = read_json(ROOT / "config/project-plan.json")
        self.assertEqual(85, len(plan["tasks"]))
        for items in (plan["batches"], plan["tasks"]):
            by_id = {item["id"]: item for item in items}
            self.assertEqual(len(items), len(by_id))
            resolved = set()
            remaining = set(by_id)
            while remaining:
                ready = {
                    key for key in remaining
                    if set(by_id[key]["dependsOn"]).issubset(resolved)
                }
                self.assertTrue(ready, f"Missing dependency or cycle: {remaining}")
                resolved.update(ready)
                remaining.difference_update(ready)
        accepted = [batch for batch in plan["batches"] if batch["status"] == "accepted"]
        for batch in accepted:
            self.assertEqual("pass", batch["checks"]["human"])
            self.assertIsNotNone(batch["humanAcceptance"])
        self.assertEqual("accepted", plan["batches"][0]["status"])
        b01 = plan["batches"][1]
        if b01["status"] == "accepted":
            record = read_json(ROOT / b01["humanAcceptance"]["evidence"])
            self.assertEqual("accepted", record["status"])
            self.assertEqual(b01["humanAcceptance"]["candidate"], record["candidate"])
            reviewed = ROOT / record["reviewedManifest"]
            self.assertEqual(
                record["reviewedManifestSha256"],
                hashlib.sha256(reviewed.read_bytes()).hexdigest(),
            )
            self.assertEqual("pass", b01["checks"]["human"])
            self.assertTrue(record["userStatement"].strip())
        else:
            self.assertIsNone(b01["humanAcceptance"])
            self.assertNotEqual("pass", b01["checks"]["human"])
        # Starting a new batch requires an explicit, scoped user instruction.
        # Do not freeze legitimate later work to the previous batch's planning state.
        by_batch = {batch["id"]: batch for batch in plan["batches"]}
        for batch in plan["batches"][2:]:
            if batch["status"] == "planned":
                continue
            authorization = batch["executionAuthorization"]
            record = read_json(ROOT / authorization["evidence"])
            self.assertEqual(batch["id"], record["batch"])
            self.assertEqual(batch["phase"], record["phase"])
            self.assertTrue(record["allowImplementation"])
            self.assertTrue(record["userStatement"].strip())
            self.assertEqual(authorization["userStatement"], record["userStatement"])
            self.assertFalse(record["allowPushOrRelease"])
            for dependency in batch["dependsOn"]:
                self.assertEqual("accepted", by_batch[dependency]["status"])

    def test_b00_acceptance_hashes_match_the_recorded_git_baseline(self):
        acceptance = read_json(ROOT / "docs/reviews/B00/acceptance.json")
        for item in acceptance["baselineFiles"]:
            raw = subprocess.check_output(
                ["git", "show", f"{acceptance['baselineCommit']}:{item['path']}"],
                cwd=ROOT,
            )
            # The acceptance recorded Windows working-tree bytes; Git stores LF.
            digest = hashlib.sha256(raw).hexdigest()
            crlf_digest = hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            self.assertIn(item["sha256"], (digest, crlf_digest), item["path"])


if __name__ == "__main__":
    unittest.main()
