"""Explicit rendered refraction comparison on a task-owned emulator.

Uses the same APK, calibration content, theme and navigation position for both
captures. Only refraction changes. Pixel differences prove rendered refraction,
not Apple/HyperOS visual equivalence or whole-product acceptance.
Pillow is imported only on explicit execution; discovery never operates a device.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time

from test_android_smoke import AndroidSmoke
from test_android_navigation import installed_apk_hash, night_preference, parse_geometry


def surface_geometry(rectangles):
    """Derive the fixed Miuix 0.9.4 surface, not clipped accessibility bounds.

    The app uses 24dp square icons and centered, equally tall cells. The pinned
    FloatingNavigationBar applies 12dp horizontal padding and a 52dp minimum
    height around its content. Recheck this contract when either source changes.
    Positive dp values use Kotlin roundToPx rounding, not Python's ties-to-even.
    """
    items = [rectangles[index] if index in rectangles else rectangles[str(index)]
             for index in range(3)]
    for item in items:
        for part in ("cell", "icon", "label"):
            left, top, right, bottom = item[part]
            if not all(math.isfinite(value) for value in (left, top, right, bottom)):
                raise AssertionError("Non-finite navigation layout.")
            if right <= left or bottom <= top:
                raise AssertionError("Empty navigation layout.")
    cells = [item["cell"] for item in items]
    icons = [item["icon"] for item in items]
    widths = [icon[2] - icon[0] for icon in icons]
    if any(icon[3] - icon[1] != width for icon, width in zip(icons, widths)):
        raise AssertionError("The fixed 24dp icons must be square.")
    if len(set(widths)) != 1 or len({(cell[1], cell[3]) for cell in cells}) != 1:
        raise AssertionError("The fixed icon density and cell vertical bounds must agree.")
    density = widths[0] / 24
    padding = math.floor(12 * density + 0.5)
    height = max(cells[0][3] - cells[0][1], math.floor(52 * density + 0.5))
    top = math.floor((cells[0][1] + cells[0][3] - height) / 2)
    bounds = (math.floor(min(cell[0] for cell in cells) - padding), top,
              math.ceil(max(cell[2] for cell in cells) + padding), math.ceil(top + height))
    if any(child[0] < bounds[0] or child[1] < bounds[1]
           or child[2] > bounds[2] or child[3] > bounds[3]
           for item in items for child in item.values()):
        raise AssertionError("The derived surface must contain all actual content rectangles.")
    return {
        "bounds": bounds, "densityFrom24dpIcon": density,
        "horizontalPaddingPx": padding, "minimumHeightPx": math.floor(52 * density + 0.5),
        "method": "pinned Miuix 0.9.4: cell union + 12dp horizontal padding; centered max(cell height,52dp)",
        "limitations": "Derived layout bounds for the pinned source; not an independent optical contour measurement.",
    }


def compare_images(full_path, flat_path, bounds, rectangles):
    from PIL import Image, ImageChops, ImageDraw, ImageStat

    with Image.open(full_path) as first, Image.open(flat_path) as second:
        if first.size != second.size:
            raise AssertionError("Comparison viewport sizes differ.")
        if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > first.width or bounds[3] > first.height:
            raise AssertionError("Comparison surface falls outside the screenshot.")
        first = first.convert("RGB").crop(bounds)
        second = second.convert("RGB").crop(bounds)
    width, height = first.size
    mask = Image.new("L", first.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((2, 2, width - 3, height - 3), radius=height / 2, fill=255)
    inset = max(4, round(height * 0.17))
    draw.rounded_rectangle(
        (inset, inset, width - inset - 1, height - inset - 1),
        radius=max(0, height / 2 - inset), fill=0,
    )
    for item in rectangles.values():
        for part in ("icon", "label"):
            left, top, right, bottom = item[part]
            draw.rectangle(
                (left - bounds[0] - 2, top - bounds[1] - 2,
                 right - bounds[0] + 2, bottom - bounds[1] + 2), fill=0,
            )
    pixels = ImageStat.Stat(mask).sum[0] / 255
    if pixels < 100:
        raise AssertionError("Insufficient unobstructed edge pixels for refraction comparison.")
    difference = ImageChops.difference(first, second).convert("L")
    changed = ImageChops.multiply(difference.point(lambda value: 255 if value >= 8 else 0), mask)
    fraction = (ImageStat.Stat(changed).sum[0] / 255) / pixels
    mean = ImageStat.Stat(difference, mask).mean[0]
    return {
        "edgePixels": int(pixels), "changedEdgeFractionThreshold8": fraction,
        "meanEdgeDifference": mean, "thresholdFraction": 0.10, "thresholdMean": 4.0,
        "renderedRefractionDetected": fraction >= 0.10 and mean >= 4.0,
    }


def capture(args):
    import PIL

    if re.fullmatch(r"emulator-\d+", args.serial) is None or args.api < 33:
        raise ValueError("An explicitly selected API33+ task emulator is required.")
    expected = "com.yunobase.recipe.prototype" + (".debug" if args.variant == "debug" else "")
    if args.package != expected:
        raise ValueError("Only the matching isolated prototype variant is allowed.")
    driver = AndroidSmoke(args)
    driver.prefix = f"test_b02_api{args.api}_{args.variant}_glass"
    report_path = driver.output / f"{driver.prefix}.json"
    if report_path.exists():
        raise FileExistsError("Refusing to overwrite existing comparison evidence.")
    apk_hash = hashlib.sha256(Path(args.apk).read_bytes()).hexdigest()
    rows, failure, restore_errors = [], None, []
    old_night = old_scale = None
    actual_hash = None
    device_accepted = False
    try:
        names = [line.strip() for line in driver.adb("emu", "avd", "name").splitlines()
                 if line.strip() and line.strip() != "OK"]
        driver.require(len(names) == 1 and re.fullmatch(
            rf"tmp_b02_api{args.api}_\d{{8}}_\d{{6}}", names[0]) is not None,
            "task-owned B02 AVD name matches the selected API")
        driver.require(driver.adb("shell", "getprop", "ro.build.version.sdk") == str(args.api),
                       "actual device API matches")
        actual_hash = installed_apk_hash(driver)
        driver.require(actual_hash == apk_hash, "installed APK bytes match the supplied artifact")
        device_accepted = True
        old_night = night_preference(driver)
        old_scale = driver.adb("shell", "settings", "get", "system", "font_scale")
        for night in ("no", "yes"):
            captures = {}
            for mode, disabled in (("refractive", "false"), ("blur_only", "true")):
                driver.adb("shell", "am", "force-stop", args.package)
                driver.adb("shell", "cmd", "uimode", "night", night)
                driver.adb("shell", "settings", "put", "system", "font_scale", "1.0")
                driver.require(night_preference(driver) == night, f"{night}: night preference applied")
                driver.require(driver.adb("shell", "settings", "get", "system", "font_scale") == "1.0",
                               f"{night}: font scale applied")
                result = driver.adb(
                    "shell", "am", "start", "-W", "-n",
                    f"{args.package}/com.yunobase.recipe.MainActivity",
                    "--ez", "b02.glass_calibration", "true",
                    "--ez", "b02.disable_refraction", disabled,
                )
                driver.require("Status: ok" in result, f"{night}/{mode}: calibration cold start; {result}")
                calibration = driver.wait_node("b02_glass_calibration")
                surface = driver.wait_node("b02_material_surface")
                time.sleep(0.5)
                logs = driver.logs()
                driver.require("material=enhanced" in logs and "material=clear" not in logs
                               and "effect-failed" not in logs and "FATAL EXCEPTION" not in logs,
                               f"{night}/{mode}: enhanced pipeline remains active without a fallback")
                desired = "false" if disabled == "true" else "true"
                driver.require(f"glass-pipeline; refraction={desired};" in logs,
                               f"{night}/{mode}: actual effects callback confirms requested mode")
                suffix = ("dark" if night == "yes" else "light") + "_" + mode
                path = driver.output / f"{driver.prefix}_{suffix}.png"
                if path.exists():
                    raise FileExistsError(f"Refusing to overwrite {path}")
                driver.screenshot(suffix)
                log_path = driver.output / f"{driver.prefix}_{suffix}_log.txt"
                if log_path.exists():
                    raise FileExistsError(f"Refusing to overwrite {log_path}")
                log_path.write_text(logs + "\n", encoding="utf-8")
                rectangles, _ = parse_geometry(logs)
                geometry = surface_geometry(rectangles)
                captures[mode] = {
                    "path": path.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bounds": geometry["bounds"], "surfaceGeometry": geometry,
                    "semanticBounds": driver.bounds(surface), "rectangles": rectangles,
                    "calibrationBounds": driver.bounds(calibration),
                    "log": log_path.as_posix(),
                }
            driver.require(captures["refractive"]["bounds"] == captures["blur_only"]["bounds"],
                           f"{night}: both modes use the exact same navigation viewport")
            driver.require(captures["refractive"]["rectangles"] == captures["blur_only"]["rectangles"]
                           and captures["refractive"]["calibrationBounds"] == captures["blur_only"]["calibrationBounds"],
                           f"{night}: all nine control rectangles and calibration bounds remain unchanged")
            from PIL import Image, ImageChops
            calibration_bounds = captures["refractive"]["calibrationBounds"]
            navigation_bounds = captures["refractive"]["bounds"]
            reference_bounds = (
                calibration_bounds[0] + 10, calibration_bounds[1] + 20,
                calibration_bounds[2] - 10, navigation_bounds[1] - 40,
            )
            driver.require(reference_bounds[3] > reference_bounds[1],
                           f"{night}: unobstructed background reference is available")
            with Image.open(captures["refractive"]["path"]) as full, Image.open(captures["blur_only"]["path"]) as flat:
                full_reference = full.convert("RGB").crop(reference_bounds)
                flat_reference = flat.convert("RGB").crop(reference_bounds)
                driver.require(ImageChops.difference(full_reference, flat_reference).getbbox() is None,
                               f"{night}: calibration pixels outside glass are byte-identical")
            metrics = compare_images(
                captures["refractive"]["path"], captures["blur_only"]["path"],
                captures["refractive"]["bounds"], captures["refractive"]["rectangles"],
            )
            rows.append({"night": night, "captures": captures, "pixelComparison": metrics})
            driver.require(metrics["renderedRefractionDetected"],
                           f"{night}: rendered edge refraction differs from blur-only; metrics={metrics}")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if device_accepted:
            try:
                driver.adb("shell", "am", "force-stop", args.package)
            except Exception as error:
                restore_errors.append(f"stop-before-restore: {error}")
        for key, value in (("night", old_night), ("font", old_scale)):
            if value is None:
                continue
            try:
                if key == "night":
                    driver.adb("shell", "cmd", "uimode", "night", value)
                    if night_preference(driver) != value:
                        raise AssertionError("Night preference restoration failed.")
                else:
                    driver.adb("shell", "settings", "delete" if value == "null" else "put",
                               "system", "font_scale", *([] if value == "null" else [value]))
                    if driver.adb("shell", "settings", "get", "system", "font_scale") != value:
                        raise AssertionError("Font preference restoration failed.")
            except Exception as error:
                restore_errors.append(f"{key}: {type(error).__name__}: {error}")
        if device_accepted:
            try:
                driver.adb("shell", "am", "force-stop", args.package)
            except Exception as error:
                restore_errors.append(f"force-stop: {error}")
    status = "pass" if failure is None and not restore_errors else "fail"
    report = {
        "candidate": args.candidate, "api": args.api, "variant": args.variant, "status": status,
        "apkSha256": apk_hash, "installedApkSha256": actual_hash, "pillowVersion": PIL.__version__,
        "checks": driver.results, "rows": rows, "failure": failure, "restoreErrors": restore_errors,
        "restoredPreferences": {"font": old_scale, "night": old_night},
        "limitations": [
            "Controlled high-contrast fixture proves rendered refraction; not a brand-equivalence test.",
            "No physical-device, GPU performance or complete accessibility acceptance.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"api": args.api, "status": status, "failure": failure, "restoreErrors": restore_errors}))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--api", type=int, choices=(33, 37), required=True)
    parser.add_argument("--apk", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--variant", choices=("debug", "release"), required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--candidate", default="B02-candidate-3")
    raise SystemExit(capture(parser.parse_args()))
