"""Public-catalog byte integrity regressions; fixtures are not publishable food data."""
from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("test_catalog_integrity_tool", ROOT / "scripts/catalog_integrity.py")
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
SAMPLES = json.loads((ROOT / "tests/test_contract_samples.json").read_text(encoding="utf-8"))


class CatalogIntegrityTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / ".agent-tmp/b01_hash"
        base.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temporary = tempfile.TemporaryDirectory(prefix=f"tmp_b01_hash_tests_{stamp}_", dir=base)
        self.workspace = Path(self.temporary.name).absolute()
        self.assertEqual(base.resolve(), self.workspace.resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = self.workspace / "public"
        self.root.mkdir()
        self.plan_path = self.workspace / "plan.json"
        self.catalog_path = self.root / "catalog.json"
        self.plan = {"revision": "test_catalog_1", "generatedAt": "2026-10-30T00:00:00Z", "entries": []}
        self.save_plan()

    def save_plan(self):
        self.plan_path.write_bytes((json.dumps(self.plan, ensure_ascii=False) + "\n").encode("utf-8"))

    def add_source(self, kind="ingredient", identity="test_entry", path=None, bom=False, crlf=False):
        relative = path or f"{kind}.json"
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source = copy.deepcopy(SAMPLES[kind])
        raw = (json.dumps(source, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if crlf:
            raw = raw.replace(b"\n", b"\r\n")
        if bom:
            raw = b"\xef\xbb\xbf" + raw
        target.write_bytes(raw)
        self.plan["entries"].append({"operation": "upsert", "libraryEntryId": identity, "kind": kind, "path": relative})
        self.save_plan()
        return target, raw

    def build(self):
        return TOOL.build_catalog(self.plan_path, self.root, self.catalog_path)

    def publish_fixture(self):
        catalog, inputs = self.build()
        TOOL.write_catalog(self.catalog_path, catalog)
        return catalog, {**inputs, self.catalog_path: self.catalog_path.read_bytes()}

    def cli(self, command="verify", *extra):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return TOOL.main([command, "--plan", str(self.plan_path), "--root", str(self.root),
                              "--catalog", str(self.catalog_path), *extra])

    def git(self, *args):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
        result = subprocess.run(
            ["git", "-c", "user.name=Catalog Test", "-c", "user.email=test@example.invalid",
             "-c", "core.safecrlf=false", *args],
            cwd=self.workspace, env=env, capture_output=True, timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8", errors="replace"))
        return result.stdout

    def init_git(self):
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")

    def test_raw_sha256_preserves_bom_crlf_and_independent_sources(self):
        first, first_raw = self.add_source("recipe", "test_recipe_a", "recipe_a.json", bom=True, crlf=True)
        second, second_raw = self.add_source("ingredient", "test_ingredient", bom=True)
        catalog, _ = self.publish_fixture()
        for entry, path, raw in zip(catalog["entries"], (first, second), (first_raw, second_raw)):
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["contentHash"])
            self.assertEqual(raw, path.read_bytes())
        self.assertEqual(0, self.cli())
        self.assertEqual(first_raw, first.read_bytes())

    def test_same_hash_and_same_payload_path_keep_distinct_library_entries(self):
        self.add_source()
        duplicate = dict(self.plan["entries"][0], libraryEntryId="test_entry_b")
        self.plan["entries"].append(duplicate)
        self.save_plan()
        catalog, _ = self.publish_fixture()
        self.assertEqual(["test_entry", "test_entry_b"], [x["libraryEntryId"] for x in catalog["entries"]])
        self.assertEqual(catalog["entries"][0]["contentHash"], catalog["entries"][1]["contentHash"])
        self.assertEqual(0, self.cli())

    def test_decimal_summary_round_trip_never_uses_binary_float(self):
        path, _ = self.add_source()
        source = SAMPLES["ingredient"] | {"per100": SAMPLES["ingredient"]["per100"] | {"carb": 0.07}}
        path.write_text(json.dumps(source), encoding="utf-8")
        catalog, _ = self.publish_fixture()
        self.assertEqual(Decimal("0.07"), catalog["entries"][0]["summary"]["per100"]["carb"])
        actual = TOOL.parse_json(self.catalog_path.read_bytes())
        self.assertEqual(Decimal("0.07"), actual["entries"][0]["summary"]["per100"]["carb"])
        self.assertEqual(0, self.cli())

    def test_tampered_payload_is_rejected_without_repair(self):
        path, raw = self.add_source()
        self.publish_fixture()
        changed = raw + b"\n"
        path.write_bytes(changed)
        catalog_before = self.catalog_path.read_bytes()
        self.assertEqual(2, self.cli())
        self.assertEqual(changed, path.read_bytes())
        self.assertEqual(catalog_before, self.catalog_path.read_bytes())

    def test_tampered_summary_and_plan_are_rejected(self):
        self.add_source()
        catalog, _ = self.publish_fixture()
        tampered = copy.deepcopy(catalog)
        tampered["entries"][0]["summary"]["name"] = "TAMPERED"
        TOOL.write_catalog(self.catalog_path, tampered)
        self.assertEqual(2, self.cli())
        TOOL.write_catalog(self.catalog_path, catalog)
        self.plan["entries"][0]["libraryEntryId"] = "test_other_identity"
        self.save_plan()
        self.assertEqual(2, self.cli())

    def test_invalid_json_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(TOOL.IntegrityError):
                TOOL.parse_json(raw)

    def test_legacy_recipe_cannot_enter_public_catalog(self):
        target, _ = self.add_source("recipe")
        legacy = json.loads(next((ROOT / "data/reference/recipes").glob("*.json")).read_text(encoding="utf-8-sig"))
        target.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(TOOL.IntegrityError):
            self.build()

    def test_unsafe_paths_and_catalog_self_reference_are_rejected(self):
        self.add_source()
        for relative in ("../ingredient.json", "/ingredient.json", "a/../ingredient.json",
                         r"a\ingredient.json", "a/%2e%2e.json", "catalog.json"):
            with self.subTest(path=relative):
                self.plan["entries"][0]["path"] = relative
                self.save_plan()
                with self.assertRaises(TOOL.IntegrityError):
                    self.build()

    def test_missing_unlisted_payloads_and_duplicate_identity_are_rejected(self):
        target, raw = self.add_source()
        self.plan["entries"].append(dict(self.plan["entries"][0]))
        self.save_plan()
        with self.assertRaises(TOOL.IntegrityError):
            self.build()
        self.plan["entries"].pop()
        self.save_plan()
        extra = self.root / "unlisted.json"
        extra.write_bytes(raw)
        with self.assertRaises(TOOL.IntegrityError):
            self.build()
        extra.unlink()
        target.unlink()
        with self.assertRaises(TOOL.IntegrityError):
            self.build()

    def test_symlink_or_reparse_component_is_rejected(self):
        target, _ = self.add_source()
        link = self.root / "linked"
        try:
            link.symlink_to(self.workspace, target_is_directory=True)
        except OSError:
            original = Path.lstat
            def fake_lstat(path, *args, **kwargs):
                if path == target:
                    return SimpleNamespace(st_mode=0o100644, st_file_attributes=0x400)
                return original(path, *args, **kwargs)
            with patch.object(Path, "lstat", fake_lstat), self.assertRaises(TOOL.IntegrityError):
                self.build()
        else:
            try:
                with self.assertRaises(TOOL.IntegrityError):
                    self.build()
            finally:
                link.unlink()

    def test_explicit_delete_survives_and_omission_is_not_deletion(self):
        self.add_source()
        previous, _ = self.publish_fixture()
        deleted = {"operation": "delete", "libraryEntryId": "test_entry", "kind": "ingredient",
                   "id": SAMPLES["ingredient"]["id"], "revision": "test_delete_2",
                   "deletedAt": "2026-10-30T01:00:00Z"}
        self.plan.update(revision="test_catalog_2", entries=[deleted])
        self.save_plan()
        (self.root / "ingredient.json").unlink()
        current, _ = self.build()
        TOOL.check_previous(current, previous)
        self.assertEqual([deleted], current["entries"])
        TOOL.check_previous(current, current)
        missing = dict(current, revision="test_catalog_3", entries=[])
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.check_previous(missing, previous)

    def test_changed_bytes_require_both_source_and_catalog_new_revisions(self):
        path, _ = self.add_source()
        previous, _ = self.publish_fixture()
        source = copy.deepcopy(SAMPLES["ingredient"])
        source["name"] += " changed"
        path.write_text(json.dumps(source), encoding="utf-8")
        changed, _ = self.build()
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.check_previous(changed, previous)
        self.plan["revision"] = "test_catalog_2"
        self.save_plan()
        changed, _ = self.build()
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.check_previous(changed, previous)
        source["revision"] = "test_r2"
        path.write_text(json.dumps(source), encoding="utf-8")
        changed, _ = self.build()
        TOOL.check_previous(changed, previous)

    def test_failed_build_and_atomic_replace_preserve_previous_catalog(self):
        path, _ = self.add_source()
        catalog, _ = self.publish_fixture()
        original = self.catalog_path.read_bytes()
        path.write_bytes(b"{}")
        self.assertEqual(2, self.cli("build"))
        self.assertEqual(original, self.catalog_path.read_bytes())
        with patch.object(TOOL.os, "replace", side_effect=OSError("test atomic failure")):
            with self.assertRaises(OSError):
                TOOL.write_catalog(self.catalog_path, catalog)
        self.assertEqual(original, self.catalog_path.read_bytes())
        self.assertEqual([], list(self.root.glob("tmp_catalog_integrity_write_*")))

    def test_git_untracked_staged_and_head_inputs_match_exact_bytes(self):
        self.add_source(bom=True, crlf=True)
        _, inputs = self.publish_fixture()
        self.init_git()
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.verify_git_inputs(inputs, self.root, "staged")
        self.git("add", "--all")
        TOOL.verify_git_inputs(inputs, self.root, "staged")
        for path, original in inputs.items():
            with self.subTest(input=path.name):
                changed = original + b"\n"
                path.write_bytes(changed)
                with self.assertRaises(TOOL.IntegrityError):
                    TOOL.verify_git_inputs(inputs | {path: changed}, self.root, "staged")
                path.write_bytes(original)
        self.git("commit", "-qm", "测试哈希输入")
        TOOL.verify_git_inputs(inputs, self.root, "head")
        self.assertEqual(0, self.cli("verify", "--git-mode", "head", "--baseline-ref", "HEAD"))

    def test_git_crlf_conversion_is_detected_and_byte_attributes_prevent_it(self):
        self.add_source(crlf=True)
        _, inputs = self.publish_fixture()
        self.init_git()
        self.git("config", "core.autocrlf", "true")
        self.git("add", "--all")
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.verify_git_inputs(inputs, self.root, "staged")
        attributes = self.workspace / ".gitattributes"
        attributes.write_bytes(b"/public/** -text -filter -ident -working-tree-encoding\n/plan.json -text -filter -ident -working-tree-encoding\n")
        self.git("add", "--all")
        self.git("add", "--renormalize", "--", ".")
        TOOL.verify_git_inputs(inputs, self.root, "staged")

    def test_referenced_image_is_required_in_git_and_must_match_staged_bytes(self):
        source_path, _ = self.add_source()
        source = copy.deepcopy(SAMPLES["ingredient"])
        source["image"] = "images/test.png"
        source_path.write_text(json.dumps(source), encoding="utf-8")
        image = self.root / "images/test.png"
        image.parent.mkdir()
        image.write_bytes(b"\x89PNG\r\nTEST original image")
        _, inputs = self.publish_fixture()
        self.assertIn(image, inputs)
        self.init_git()
        self.git("add", "--", "plan.json", "public/ingredient.json", "public/catalog.json")
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.verify_git_inputs(inputs, self.root, "staged")
        self.git("add", "--", "public/images/test.png")
        TOOL.verify_git_inputs(inputs, self.root, "staged")
        image.write_bytes(b"\x89PNG\r\nTEST changed image")
        self.assertEqual(2, self.cli("verify", "--git-mode", "staged"))

    def test_extreme_integer_and_unicode_surrogate_fail_with_controlled_cli_status(self):
        giant = b'{"revision":' + b"1" * 5000 + b',"generatedAt":"2026-10-30T00:00:00Z","entries":[]}'
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.parse_json(giant)
        self.plan_path.write_bytes(giant)
        self.assertEqual(2, self.cli("build"))
        self.save_plan()
        source_path, _ = self.add_source()
        self.publish_fixture()
        previous_catalog = self.catalog_path.read_bytes()
        source = copy.deepcopy(SAMPLES["ingredient"])
        source["name"] = "\ud800"
        source_path.write_bytes(json.dumps(source, ensure_ascii=True).encode("ascii"))
        for command in ("build", "verify"):
            with self.subTest(command=command):
                self.assertEqual(2, self.cli(command))
                self.assertEqual(previous_catalog, self.catalog_path.read_bytes())
        with self.assertRaises(TOOL.IntegrityError):
            TOOL.encode_json("\ud800")

    def test_git_blob_verification_uses_constant_number_of_processes(self):
        self.add_source()
        _, small_inputs = self.publish_fixture()
        self.init_git()
        self.git("add", "--all")
        runner = TOOL.subprocess.run
        with patch.object(TOOL.subprocess, "run", wraps=runner) as small:
            TOOL.verify_git_inputs(small_inputs, self.root, "staged")
        for index in range(8):
            self.add_source(identity=f"test_extra_{index}", path=f"ingredient_{index}.json")
        self.plan["revision"] = "test_catalog_2"
        self.save_plan()
        _, large_inputs = self.publish_fixture()
        self.git("add", "--all")
        with patch.object(TOOL.subprocess, "run", wraps=runner) as large:
            TOOL.verify_git_inputs(large_inputs, self.root, "staged")
        self.assertGreater(len(large_inputs), len(small_inputs))
        self.assertEqual(4, small.call_count)
        self.assertEqual(small.call_count, large.call_count)
        commands = [call.args[0] for call in large.call_args_list]
        self.assertEqual(1, sum(command[1:3] == ["cat-file", "--batch-check"] for command in commands))
        self.assertEqual(1, sum(command[1:3] == ["cat-file", "--batch"] for command in commands))

    def test_zero_before_ref_has_no_root_baseline_then_uses_parent_catalog(self):
        self.add_source()
        previous, _ = self.publish_fixture()
        self.init_git()
        self.git("add", "--all")
        self.git("commit", "-qm", "测试初始目录")
        zero = "0" * 40
        self.assertIsNone(TOOL.git_baseline(self.root, self.catalog_path, zero))
        self.assertEqual(0, self.cli("verify", "--git-mode", "head", "--baseline-ref", zero))
        self.plan["revision"] = "test_catalog_2"
        self.save_plan()
        self.assertEqual(0, self.cli("build"))
        self.git("add", "--all")
        self.git("commit", "-qm", "测试后续目录")
        self.assertEqual(previous, TOOL.git_baseline(self.root, self.catalog_path, zero))
        self.assertEqual(0, self.cli("verify", "--git-mode", "head", "--baseline-ref", zero))

    def test_enormous_positive_and_negative_exponents_fail_with_controlled_status(self):
        for exponent in (b"+9999999999999999999", b"-9999999999999999999"):
            raw = b'{"revision":1e' + exponent + b',"generatedAt":"2026-10-30T00:00:00Z","entries":[]}'
            with self.subTest(exponent=exponent):
                with self.assertRaises(TOOL.IntegrityError):
                    TOOL.parse_json(raw)
                self.plan_path.write_bytes(raw)
                for command in ("build", "verify"):
                    self.assertEqual(2, self.cli(command))

    def test_old_larger_staged_blob_is_rejected_before_contents_are_requested(self):
        path = self.root / "test_large.bin"
        path.write_bytes(b"x" * (128 * 1024))
        self.init_git()
        self.git("add", "--all")
        path.write_bytes(b"x")
        runner = TOOL.subprocess.run
        def guarded_run(command, *args, **kwargs):
            if command[1:3] == ["cat-file", "--batch"]:
                self.fail("Oversized old Git content must never be requested")
            return runner(command, *args, **kwargs)
        with patch.object(TOOL.subprocess, "run", side_effect=guarded_run) as calls:
            with self.assertRaises(TOOL.IntegrityError):
                TOOL.verify_git_inputs({path: path.read_bytes()}, self.root, "staged")
        commands = [call.args[0] for call in calls.call_args_list]
        self.assertEqual(["cat-file", "--batch-check"], commands[-1][1:3])
        self.assertEqual(3, calls.call_count)

    def test_shared_summary_amplification_and_final_newline_obey_output_size_limit(self):
        original_catalog, _ = self.publish_fixture()
        original_bytes = self.catalog_path.read_bytes()
        source_path, _ = self.add_source()
        source = copy.deepcopy(SAMPLES["ingredient"])
        source["name"] = "TEST " + "\u83dc" * 6000
        source_path.write_bytes(json.dumps(source, ensure_ascii=False).encode("utf-8"))
        for index in range(4):
            self.plan["entries"].append(dict(self.plan["entries"][0], libraryEntryId=f"test_shared_{index}"))
        self.plan["revision"] = "test_catalog_2"
        self.save_plan()
        self.assertLess(source_path.stat().st_size, 64 * 1024)
        with patch.object(TOOL, "MAX_FILE_BYTES", 64 * 1024):
            with self.assertRaises(TOOL.IntegrityError):
                self.build()
            self.assertEqual(2, self.cli("build"))
        self.assertEqual(original_bytes, self.catalog_path.read_bytes())
        without_newline = len(TOOL.encode_json(original_catalog).encode("utf-8"))
        with patch.object(TOOL, "MAX_FILE_BYTES", without_newline):
            with self.assertRaises(TOOL.IntegrityError):
                TOOL.write_catalog(self.catalog_path, original_catalog)
        self.assertEqual(original_bytes, self.catalog_path.read_bytes())
        self.assertEqual([], list(self.root.glob("tmp_catalog_integrity_write_*")))


if __name__ == "__main__":
    unittest.main()
