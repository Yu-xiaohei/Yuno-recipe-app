"""Explicit B02 navigation geometry checks; unittest discovery never touches devices.

Requires an already installed, matching APK on a task-owned B02 emulator. Measures
real onGloballyPositioned logs rather than inferring alignment from test node bounds.
Pass means geometry/selection checks passed, not visual or accessibility acceptance.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from test_android_smoke import AndroidSmoke


NAVIGATION_IDS = tuple(f"b02_tab_{index}" for index in range(3))
GEOMETRY_PATTERN = re.compile(
    r"nav-geometry;\s*part=(cell|icon|label);\s*index=([012]);\s*"
    r"left=([^;\s]+);\s*top=([^;\s]+);\s*"
    r"right=([^;\s]+);\s*bottom=([^;\s]+)"
)


def parse_geometry(logs):
    """Return the last actual callback for each of the nine navigation rectangles."""
    rectangles = {index: {} for index in range(3)}
    last_lines = {}
    for line in logs.splitlines():
        if "nav-geometry;" not in line:
            continue
        match = GEOMETRY_PATTERN.search(line)
        if match is None:
            raise AssertionError(f"Malformed navigation geometry callback: {line}")
        part, index, *raw_bounds = match.groups()
        bounds = tuple(float(value) for value in raw_bounds)
        if not all(math.isfinite(value) for value in bounds):
            raise AssertionError(f"Non-finite navigation geometry: {line}")
        left, top, right, bottom = bounds
        if right <= left or bottom <= top:
            raise AssertionError(f"Empty navigation geometry: {line}")
        index = int(index)
        rectangles[index][part] = bounds
        last_lines[(index, part)] = line
    missing = [
        f"{index}:{part}"
        for index in range(3)
        for part in ("cell", "icon", "label")
        if part not in rectangles[index]
    ]
    if missing:
        raise AssertionError(f"Missing actual navigation callbacks: {', '.join(missing)}")
    return rectangles, [
        last_lines[(index, part)]
        for index in range(3)
        for part in ("cell", "icon", "label")
    ]


def geometry_metrics(rectangles):
    widths = []
    items = []
    for index in range(3):
        cell = rectangles[index]["cell"]
        icon = rectangles[index]["icon"]
        label = rectangles[index]["label"]
        widths.append(cell[2] - cell[0])
        center_x = (cell[0] + cell[2]) / 2
        center_y = (cell[1] + cell[3]) / 2
        group_top = min(icon[1], label[1])
        group_bottom = max(icon[3], label[3])
        items.append({
            "index": index,
            "cell": cell,
            "icon": icon,
            "label": label,
            "iconHorizontalErrorPx": abs((icon[0] + icon[2]) / 2 - center_x),
            "labelHorizontalErrorPx": abs((label[0] + label[2]) / 2 - center_x),
            "groupVerticalErrorPx": abs((group_top + group_bottom) / 2 - center_y),
            "contentWithinCell": all(
                child[0] >= cell[0] - 1
                and child[1] >= cell[1] - 1
                and child[2] <= cell[2] + 1
                and child[3] <= cell[3] + 1
                for child in (icon, label)
            ),
        })
    return {
        "cellWidthsPx": widths,
        "cellWidthSpreadPx": max(widths) - min(widths),
        "items": items,
    }


def assert_geometry(driver, metrics, description):
    driver.require(
        metrics["cellWidthSpreadPx"] <= 1.0,
        f"{description}: three cell widths differ by at most 1px; "
        f"actual={metrics['cellWidthsPx']}",
    )
    for item in metrics["items"]:
        prefix = f"{description}: tab {item['index']}"
        for key, tolerance, name in (
            ("iconHorizontalErrorPx", 1.0, "icon horizontal center"),
            ("labelHorizontalErrorPx", 1.0, "label horizontal center"),
            ("groupVerticalErrorPx", 1.5, "icon/label group vertical center"),
        ):
            driver.require(
                item[key] <= tolerance,
                f"{prefix}: {name} error <= {tolerance}px; actual={item[key]}",
            )
        driver.require(item["contentWithinCell"], f"{prefix}: content stays within its cell")


def installed_apk_hash(driver):
    paths = driver.adb("shell", "pm", "path", driver.args.package).splitlines()
    if len(paths) != 1 or not paths[0].startswith("package:"):
        raise AssertionError("Expected one installed, monolithic prototype APK.")
    device_path = paths[0].removeprefix("package:")
    value = driver.adb("shell", "sha256sum", device_path).split()
    if not value or re.fullmatch(r"[a-fA-F0-9]{64}", value[0]) is None:
        raise AssertionError("Cannot read the installed APK's actual SHA-256.")
    return value[0].lower()


def selected_tabs(tree):
    result = {}
    for index, resource_id in enumerate(NAVIGATION_IDS):
        matches = [
            node for node in tree.iter("node")
            if node.get("resource-id") == resource_id
        ]
        if len(matches) != 1:
            raise AssertionError(f"Expected one visible {resource_id}, found {len(matches)}.")
        selected = matches[0].get("selected")
        if selected not in ("true", "false"):
            raise AssertionError(f"Selection state unavailable for {resource_id}: {selected!r}")
        result[index] = selected == "true"
    return result


def screenshot_record(driver, suffix):
    path = driver.output / f"{driver.prefix}_{suffix}.png"
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {path}")
    driver.screenshot(suffix)
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[-8:-4] != b"IEND":
        raise AssertionError(f"Screenshot is not a complete PNG: {path}")
    return {"path": path.as_posix(), "sha256": hashlib.sha256(data).hexdigest()}


def night_preference(driver):
    value = driver.adb("shell", "cmd", "uimode", "night").split(":")[-1].strip()
    if value not in ("yes", "no", "auto", "custom"):
        raise AssertionError(f"Unrecognized night preference: {value!r}")
    return value


def capture(args):
    # Validate before instantiating a driver or issuing any device command.
    if re.fullmatch(r"emulator-\d+", args.serial) is None:
        raise ValueError("Only an explicitly selected emulator is allowed.")
    if args.package not in (
        "com.yunobase.recipe.prototype", "com.yunobase.recipe.prototype.debug",
    ):
        raise ValueError("Only the isolated prototype package is allowed.")
    expected_package = "com.yunobase.recipe.prototype" + (
        ".debug" if args.variant == "debug" else ""
    )
    if args.package != expected_package:
        raise ValueError("Package does not match the requested build variant.")
    apk_path = Path(args.apk).resolve(strict=True)
    apk_hash = hashlib.sha256(apk_path.read_bytes()).hexdigest()
    driver = AndroidSmoke(args)
    driver.prefix = f"test_b02_api{args.api}_{args.variant}_navigation"
    report_path = driver.output / f"{driver.prefix}.json"
    if report_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {report_path}")

    rows = []
    failure = None
    original_scale = None
    original_night = None
    actual_installed_hash = None
    avd_name = None
    restore_errors = []
    restored = {}
    try:
        avd_output = driver.adb("emu", "avd", "name")
        names = [line.strip() for line in avd_output.splitlines()
                 if line.strip() and line.strip() != "OK"]
        driver.require(len(names) == 1, "emulator reports one explicit AVD name")
        avd_name = names[0]
        driver.require(
            re.fullmatch(rf"tmp_b02_api{args.api}_\d{{8}}_\d{{6}}", avd_name) is not None,
            f"AVD belongs to this B02 task and API: {avd_name}",
        )
        driver.require(
            driver.adb("shell", "getprop", "ro.build.version.sdk") == str(args.api),
            f"device SDK equals {args.api}",
        )
        driver.require(
            driver.adb("shell", "getprop", "sys.boot_completed") == "1",
            "device boot completed",
        )
        actual_installed_hash = installed_apk_hash(driver)
        driver.require(
            actual_installed_hash == apk_hash,
            "installed APK actual SHA-256 equals the supplied APK",
        )
        original_scale = driver.adb("shell", "settings", "get", "system", "font_scale")
        if original_scale != "null":
            original_number = float(original_scale)
            if not math.isfinite(original_number) or original_number <= 0:
                raise AssertionError(f"Unusable original font scale: {original_scale!r}")
        original_night = night_preference(driver)

        for scale in ("1.0", "2.0"):
            driver.adb("shell", "am", "force-stop", args.package)
            driver.adb("shell", "settings", "put", "system", "font_scale", scale)
            driver.require(
                float(driver.adb("shell", "settings", "get", "system", "font_scale"))
                == float(scale),
                f"font scale {scale} is applied",
            )
            driver.launch()
            for index in range(3):
                suffix = f"scale{scale.replace('.', '_')}_tab{index}"
                description = f"scale {scale}, selected tab {index}"
                driver.tap(NAVIGATION_IDS[index])
                tree = driver.ui()
                # Preserve the actual snapshot before assertions; failures remain reviewable.
                xml_path = driver.output / f"{driver.prefix}_{suffix}.xml"
                logs_path = driver.output / f"{driver.prefix}_{suffix}_layout.txt"
                for path in (xml_path, logs_path):
                    if path.exists():
                        raise FileExistsError(f"Refusing to overwrite evidence: {path}")
                xml_path.write_bytes(ET.tostring(tree, encoding="utf-8"))
                logs = driver.logs()
                logs_path.write_text(logs + "\n", encoding="utf-8")
                row = {
                    "fontScale": scale,
                    "selectedTarget": index,
                    "night": night_preference(driver),
                    "uiSnapshot": xml_path.as_posix(),
                    "layoutLog": logs_path.as_posix(),
                    "screenshot": screenshot_record(driver, suffix),
                    "status": "checking",
                }
                rows.append(row)
                selected = selected_tabs(tree)
                row["selected"] = selected
                driver.require(
                    selected == {target: target == index for target in range(3)},
                    f"{description}: only the actual tapped tab is selected",
                )
                rectangles, last_lines = parse_geometry(logs)
                row["lastLayoutCallbacks"] = last_lines
                row["geometry"] = geometry_metrics(rectangles)
                assert_geometry(driver, row["geometry"], description)
                driver.require("FATAL EXCEPTION" not in logs, f"{description}: process has no fatal exception")
                row["status"] = "pass"
        driver.require(
            installed_apk_hash(driver) == apk_hash,
            "installed APK remains the same after geometry checks",
        )
        driver.require(
            hashlib.sha256(apk_path.read_bytes()).hexdigest() == apk_hash,
            "input APK bytes remain unchanged during geometry checks",
        )
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
        if rows and rows[-1]["status"] == "checking":
            rows[-1]["status"] = "fail"
    finally:
        # Never mutate a device rejected by the ownership/API/hash preflight.
        if original_night is not None:
            operations = [
                ("stopBeforeRestore", lambda: driver.adb("shell", "am", "force-stop", args.package)),
                ("night", lambda: driver.adb("shell", "cmd", "uimode", "night", original_night)),
                ("fontScale", lambda: driver.adb(
                    "shell", "settings",
                    "delete" if original_scale == "null" else "put",
                    "system", "font_scale",
                    *(() if original_scale == "null" else (original_scale,)),
                )),
                ("stopAfterRestore", lambda: driver.adb("shell", "am", "force-stop", args.package)),
            ]
            for name, operation in operations:
                try:
                    operation()
                except Exception as error:
                    restore_errors.append(f"{name}: {type(error).__name__}: {error}")
            try:
                restored["fontScale"] = driver.adb("shell", "settings", "get", "system", "font_scale")
                restored["night"] = night_preference(driver)
                if restored["fontScale"] != original_scale or restored["night"] != original_night:
                    restore_errors.append(
                        f"Restored preferences differ: original={original_scale}/{original_night}; "
                        f"actual={restored['fontScale']}/{restored['night']}"
                    )
            except Exception as error:
                restore_errors.append(f"readback: {type(error).__name__}: {error}")

    status = "pass" if failure is None and not restore_errors else "fail"
    report = {
        "candidate": args.candidate,
        "status": status,
        "scope": "navigation-geometry-and-selection-only-not-visual-acceptance",
        "api": args.api,
        "serial": args.serial,
        "avdName": avd_name,
        "variant": args.variant,
        "package": args.package,
        "apkSha256": apk_hash,
        "installedApkSha256": actual_installed_hash,
        "tolerancesPx": {"cellWidthSpread": 1.0, "horizontalCenter": 1.0, "groupVerticalCenter": 1.5},
        "checks": driver.results,
        "rows": rows,
        "failure": failure,
        "transientUiDumpRetries": driver.ui_retries,
        "originalPreferences": {"fontScale": original_scale, "night": original_night},
        "restoredPreferences": restored,
        "restoreErrors": restore_errors,
        "limitations": [
            "Real layout callbacks and actual taps; not screenshot pixel equality.",
            "Current night preference, font scales 1.0/2.0 and three tabs only.",
            "No physical vivo, Chinese IME, broad GPU or complete accessibility approval.",
            "No installation or package replacement; the supplied APK must already be installed.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "api": args.api, "variant": args.variant, "status": status,
        "rows": len(rows), "failure": failure, "restoreErrors": restore_errors,
    }, ensure_ascii=False))
    return 0 if status == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--api", required=True, type=int, choices=(31, 32, 33, 37))
    parser.add_argument("--apk", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--variant", required=True, choices=("debug", "release"))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--candidate", default="B02-candidate-3")
    return capture(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
