"""Build or verify public catalog SHA-256 values without rewriting source files."""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, DecimalException
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PROJECT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 10000
SAFE_PATH = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*(?:/[A-Za-z0-9_-][A-Za-z0-9._-]*)*")


class IntegrityError(ValueError):
    pass


def parse_json(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise IntegrityError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_):
        raise IntegrityError("Non-finite JSON number")

    if len(raw) > MAX_FILE_BYTES:
        raise IntegrityError("JSON file exceeds size limit")
    try:
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                          parse_float=Decimal, parse_constant=reject_constant)
    except (UnicodeError, ValueError, DecimalException, RecursionError) as exc:
        raise IntegrityError("Invalid UTF-8 JSON") from exc


def encode_json(value):
    """Deterministic exact-decimal JSON; never round through binary float."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeError as exc:
            raise IntegrityError("Invalid Unicode string") from exc
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, Decimal)):
        if isinstance(value, Decimal) and not value.is_finite():
            raise IntegrityError("Non-finite decimal")
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(encode_json(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(encode_json(k) + ":" + encode_json(v)
                              for k, v in value.items()) + "}"
    raise IntegrityError("Unsupported JSON value")


def checked_path(path: Path):
    """Reject links/junctions in every existing component before resolving."""
    path = Path(os.path.abspath(path))
    for part in (*reversed(path.parents), path):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise IntegrityError("Symlink or reparse point is not permitted")
    return path


def within(root: Path, relative: str):
    if not isinstance(relative, str) or not SAFE_PATH.fullmatch(relative):
        raise IntegrityError("Unsafe publication path")
    path = checked_path(root / relative)
    if not path.is_relative_to(root):
        raise IntegrityError("Publication path escapes root")
    return path


def read_bytes(path: Path):
    checked_path(path)
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise IntegrityError("Missing file or file exceeds size limit")
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise IntegrityError("File exceeds size limit")
    return raw


def validator(name, fragment=""):
    schemas = [parse_json(p.read_bytes()) for p in sorted((PROJECT / "schemas").glob("*.schema.json"))]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    checker = FormatChecker()
    if not {"date", "date-time", "uri"}.issubset(checker.checkers):
        raise IntegrityError("Install the pinned format-checker dependencies")
    return Draft202012Validator(
        {"$ref": f"https://yuno-recipe.invalid/schemas/{name}.schema.json{fragment}"},
        registry=registry, format_checker=checker,
    )


def validate(name, value, fragment=""):
    try:
        valid = validator(name, fragment).is_valid(value)
    except DecimalException as exc:
        raise IntegrityError("Numeric precision/exponent exceeds validator limits") from exc
    if not valid:
        raise IntegrityError(f"{name} canonical/structure validation failed")


def build_catalog(plan_path: Path, root: Path, catalog_path: Path):
    root = checked_path(root)
    catalog_path = checked_path(catalog_path)
    plan_path = checked_path(plan_path)
    if not root.is_dir() or not catalog_path.is_relative_to(root):
        raise IntegrityError("Catalog must be inside the existing publication root")
    if plan_path.is_relative_to(root) or plan_path == catalog_path:
        raise IntegrityError("Publication plan must be outside the public root")
    plan_raw = read_bytes(plan_path)
    plan = parse_json(plan_raw)
    if not isinstance(plan, dict) or set(plan) != {"revision", "generatedAt", "entries"}:
        raise IntegrityError("Plan requires exactly revision/generatedAt/entries")
    if not isinstance(plan["entries"], list) or len(plan["entries"]) > MAX_ENTRIES:
        raise IntegrityError("Invalid plan entries or entry limit exceeded")
    catalog = {"schemaVersion": 1, "kind": "catalog", "revision": plan["revision"],
               "generatedAt": plan["generatedAt"], "entries": []}
    output_bytes = len(encode_json(catalog).encode("utf-8"))
    inputs = {plan_path: plan_raw}
    total_bytes = len(plan_raw)
    ids = set()
    recipe_fields = ("name", "dishType", "tags", "image", "includesStaple", "publishedAt")
    ingredient_fields = ("name", "foodState", "defaultPortionWeight", "per100", "tags", "image", "publishedAt")
    payloads = set()
    for entry in plan["entries"]:
        if not isinstance(entry, dict):
            raise IntegrityError("Each plan entry must be an object")
        if entry.get("operation") == "delete":
            if set(entry) != {"operation", "libraryEntryId", "kind", "id", "revision", "deletedAt"}:
                raise IntegrityError("Invalid explicit deletion entry")
            output = dict(entry)
        else:
            if set(entry) != {"operation", "libraryEntryId", "kind", "path"} or entry["operation"] != "upsert":
                raise IntegrityError("Upsert plan requires operation/libraryEntryId/kind/path")
            kind = entry["kind"]
            if kind not in ("recipe", "ingredient"):
                raise IntegrityError("Unsupported source kind")
            path = within(root, entry["path"])
            if path == catalog_path or path.suffix != ".json":
                raise IntegrityError("Catalog cannot reference itself; JSON payload required")
            raw = inputs.get(path)
            if raw is None:
                raw = read_bytes(path)
                inputs[path] = raw
                total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_BYTES:
                raise IntegrityError("Publication input byte limit exceeded")
            digest = hashlib.sha256(raw).hexdigest()
            source = parse_json(raw)
            validate(kind, source, "#/$defs/canonical" if kind == "recipe" else "")
            fields = recipe_fields if kind == "recipe" else ingredient_fields
            summary = {key: source[key] for key in fields}
            if kind == "recipe":
                summary.update(weight=source["totals"]["weight"], energy=source["totals"]["energy"])
            if source["image"] is not None:
                image = within(root, source["image"])
                if image not in inputs:
                    image_raw = read_bytes(image)
                    inputs[image] = image_raw
                    total_bytes += len(image_raw)
                    if total_bytes > MAX_TOTAL_BYTES:
                        raise IntegrityError("Publication input byte limit exceeded")
            output = {"operation": "upsert", "libraryEntryId": entry["libraryEntryId"], "kind": kind,
                      "id": source["id"], "revision": source["revision"],
                      "contentHash": digest, "path": entry["path"], "summary": summary}
            payloads.add(path)
        identity = output["libraryEntryId"]
        if not isinstance(identity, str) or identity in ids:
            raise IntegrityError("Duplicate or invalid libraryEntryId")
        ids.add(identity)
        output_bytes += len(encode_json(output).encode("utf-8")) + bool(catalog["entries"])
        if output_bytes > MAX_FILE_BYTES:
            raise IntegrityError("Generated catalog exceeds size limit")
        catalog["entries"].append(output)
    validate("catalog", catalog)
    # Fail closed when a new file was copied in but omitted from the plan.
    actual = set()
    def walk_error(error):
        raise IntegrityError("Cannot enumerate publication root") from error

    for directory, subdirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in (*subdirs, *files):
            path = checked_path(Path(directory) / name)
            if path.suffix.lower() == ".json" and path.is_file() and path != catalog_path:
                actual.add(path)
    if actual != payloads:
        raise IntegrityError("Unlisted or missing public JSON payload")
    return catalog, inputs


def check_previous(current, previous):
    validate("catalog", previous)
    prior = {item["libraryEntryId"]: item for item in previous["entries"]}
    if len(prior) != len(previous["entries"]):
        raise IntegrityError("Duplicate libraryEntryId in previous catalog")
    latest = {item["libraryEntryId"]: item for item in current["entries"]}
    if set(prior) - set(latest):
        raise IntegrityError("Previous records cannot disappear; use explicit delete")
    if current != previous and current["revision"] == previous["revision"]:
        raise IntegrityError("Catalog changes require a new catalog revision")
    for identity in prior.keys() & latest.keys():
        old, new = prior[identity], latest[identity]
        changed = old["operation"] != new["operation"] or (
            new["operation"] == "upsert" and old.get("contentHash") != new["contentHash"]
        ) or (new["operation"] == "delete" and old != new)
        if changed and old["revision"] == new["revision"]:
            raise IntegrityError("Changed source/deletion must use a new entry revision")


def git_output(args, cwd: Path):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=20)
    if result.returncode:
        raise IntegrityError("Git object lookup failed")
    return result.stdout


def git_baseline(root: Path, catalog_path: Path, ref: str):
    if not re.fullmatch(r"(?:[a-f0-9]{40}|HEAD|HEAD\^)", ref):
        raise IntegrityError("Invalid baseline ref")
    if ref == "0" * 40:
        # Only the main-branch push workflow uses "before". Feature branches use
        # pull_request base SHA. A new main has no remote predecessor.
        parent = git_output(["rev-list", "--parents", "-n", "1", "HEAD"], root).split()
        if len(parent) == 1:
            return None
        ref = "HEAD^"
    repo = Path(os.fsdecode(git_output(["rev-parse", "--show-toplevel"], root)).strip())
    rel = catalog_path.relative_to(repo).as_posix()
    git_output(["rev-parse", "--verify", ref + "^{commit}"], repo)
    exists = git_output(["ls-tree", "-z", ref, "--", rel], repo)
    if not exists:
        return None  # First catalog in an existing reviewed repository.
    if not exists.startswith(b"100644 ") and not exists.startswith(b"100755 "):
        raise IntegrityError("Baseline catalog must be a regular Git blob")
    return parse_json(git_output(["show", f"{ref}:{rel}"], repo))


def verify_git_inputs(inputs, root: Path, mode: str):
    repo = Path(os.fsdecode(git_output(["rev-parse", "--show-toplevel"], root)).strip())
    listing = git_output(
        ["ls-files", "--stage", "-z"] if mode == "staged"
        else ["ls-tree", "-r", "-z", "HEAD"], repo,
    )
    records = {}
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        records.setdefault(path, []).append(metadata.split())
    wanted = {}
    for path, raw in inputs.items():
        if not path.is_relative_to(repo):
            raise IntegrityError("Publication input must be in the Git repository")
        rel = path.relative_to(repo).as_posix().encode("utf-8")
        matches = records.get(rel, [])
        if len(matches) != 1 or matches[0][0] not in (b"100644", b"100755"):
            raise IntegrityError("Input is untracked, unmerged or not a regular Git file")
        metadata = matches[0]
        if mode == "staged" and metadata[2] != b"0":
            raise IntegrityError("Unmerged Git input")
        oid = metadata[1] if mode == "staged" else metadata[2]
        if oid in wanted and wanted[oid] != raw:
            raise IntegrityError("Git object maps to inconsistent input bytes")
        wanted[oid] = raw
    # Check old object sizes before requesting any contents, so a small working
    # file cannot make us load an unbounded historical/staged blob.
    query = b"".join(oid + b"\n" for oid in wanted)
    sizes = subprocess.run(
        ["git", "cat-file", "--batch-check"], cwd=repo, capture_output=True,
        input=query, timeout=20,
    )
    lines = sizes.stdout.splitlines()
    if sizes.returncode or len(lines) != len(wanted):
        raise IntegrityError("Git batch metadata read failed")
    for (oid, raw), line in zip(wanted.items(), lines):
        header = line.split()
        if len(header) != 3 or header[:2] != [oid, b"blob"] or header[2] != str(len(raw)).encode():
            raise IntegrityError("Git blob size/type differs from verified input")
    # One process for all contents, rather than two processes per file.
    result = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo, capture_output=True,
        input=query, timeout=20,
    )
    if result.returncode:
        raise IntegrityError("Git batch blob read failed")
    data, offset = result.stdout, 0
    for oid, raw in wanted.items():
        end = data.find(b"\n", offset)
        header = data[offset:end].split()
        if end == -1 or len(header) != 3 or header[:2] != [oid, b"blob"]:
            raise IntegrityError("Invalid Git batch response")
        size = int(header[2])
        offset = end + 1
        if data[offset:offset + size] != raw or data[offset + size:offset + size + 1] != b"\n":
            raise IntegrityError("Git blob differs from verified working-tree bytes")
        offset += size + 1
    if offset != len(data):
        raise IntegrityError("Unexpected Git batch output")


def write_catalog(path: Path, catalog):
    raw = (encode_json(catalog) + "\n").encode("utf-8")
    if len(raw) > MAX_FILE_BYTES:
        raise IntegrityError("Generated catalog exceeds size limit")
    checked_path(path)
    # Same-volume atomic replacement; validation is complete before this function.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fd, name = tempfile.mkstemp(prefix=f"tmp_catalog_integrity_write_{stamp}_", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--plan", type=Path, default=PROJECT / "config/catalog-publication.json")
    parser.add_argument("--root", type=Path, default=PROJECT / "data/public")
    parser.add_argument("--catalog", type=Path, default=PROJECT / "data/public/catalog.json")
    parser.add_argument("--git-mode", choices=("none", "staged", "head"), default="none")
    parser.add_argument("--baseline-ref")
    args = parser.parse_args(argv)
    try:
        root, catalog_path = checked_path(args.root), checked_path(args.catalog)
        expected, inputs = build_catalog(args.plan, root, catalog_path)
        # Also validate generated string encoding on the read-only verify path.
        encode_json(expected)
        if args.baseline_ref:
            previous = git_baseline(root, catalog_path, args.baseline_ref)
            if previous is not None:
                check_previous(expected, previous)
        if args.command == "build":
            if args.git_mode != "none":
                raise IntegrityError("Build cannot claim Git upload verification")
            if catalog_path.exists():
                check_previous(expected, parse_json(read_bytes(catalog_path)))
            write_catalog(catalog_path, expected)
        else:
            actual_raw = read_bytes(catalog_path)
            actual = parse_json(actual_raw)
            validate("catalog", actual)
            if actual != expected:
                raise IntegrityError("Catalog/hash/summary differs from source bytes or publication plan")
            inputs[catalog_path] = actual_raw
            if args.git_mode != "none":
                verify_git_inputs(inputs, root, args.git_mode)
        print(f"PASS: {args.command}; {len(expected['entries'])} catalog entries; "
              f"git={args.git_mode}; byte integrity only, not nutrition/license approval")
        return 0
    except (IntegrityError, OSError, subprocess.SubprocessError, RecursionError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
