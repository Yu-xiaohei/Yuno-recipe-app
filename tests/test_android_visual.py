"""Explicit B02 representative visual captures, never run by unittest discovery.

Captures are evidence for human review, not automatic pixel or accessibility approval.
Uses an already installed isolated prototype on a task-owned emulator. Restores the
device font scale and night-mode preference even when capture fails.
"""

import argparse
import hashlib
import json
from pathlib import Path

from test_android_smoke import AndroidSmoke


def capture(args):
    driver = AndroidSmoke(args)
    driver.prefix = f"test_b02_api{args.api}_{args.variant}_visual"
    if not args.serial.startswith("emulator-") or args.package not in (
        "com.yunobase.recipe.prototype", "com.yunobase.recipe.prototype.debug",
    ):
        raise ValueError("Only isolated prototype packages on emulators are allowed.")
    if driver.adb("shell", "getprop", "ro.build.version.sdk") != str(args.api):
        raise ValueError("Device API does not match the requested evidence.")
    apk_hash = hashlib.sha256(Path(args.apk).read_bytes()).hexdigest()
    installed_paths = driver.adb("shell", "pm", "path", args.package).splitlines()
    if len(installed_paths) != 1 or not installed_paths[0].startswith("package:"):
        raise ValueError("Expected the installed, monolithic prototype APK.")
    device_path = installed_paths[0].removeprefix("package:")
    installed_hash = driver.adb("shell", "sha256sum", device_path).split()[0]
    if installed_hash != apk_hash:
        raise ValueError("Installed APK bytes differ from --apk; run the matching smoke install first.")
    original_scale = driver.adb("shell", "settings", "get", "system", "font_scale")
    original_night = driver.adb("shell", "cmd", "uimode", "night").split(":")[-1].strip()
    if original_night not in ("yes", "no", "auto", "custom"):
        raise ValueError(f"Unrecognized original night preference: {original_night}")
    rows = []
    failure = None
    try:
        for night in ("no", "yes"):
            for scale in ("1.0", "1.3", "2.0"):
                # Prevent a live Activity from recreating while its configuration changes.
                driver.adb("shell", "am", "force-stop", args.package)
                driver.adb("shell", "cmd", "uimode", "night", night)
                driver.adb("shell", "settings", "put", "system", "font_scale", scale)
                if driver.adb("shell", "cmd", "uimode", "night").split(":")[-1].strip() != night:
                    raise AssertionError("Night preference did not apply.")
                if float(driver.adb("shell", "settings", "get", "system", "font_scale")) != float(scale):
                    raise AssertionError("Font scale did not apply.")
                driver.launch()
                suffix = f"{'dark' if night == 'yes' else 'light'}_scale{scale.replace('.', '_')}"
                driver.screenshot(suffix + "_home")
                driver.tap("b02_tab_0")
                driver.wait_node("b02_meal_overview")
                driver.screenshot(suffix + "_meals")
                driver.tap("b02_tab_2")
                driver.wait_node("b02_settings_list")
                driver.screenshot(suffix + "_settings")
                rows.append({"night": night, "fontScale": scale, "capture": "complete",
                             "screens": ["home", "meals", "settings"], "prefix": suffix})
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        driver.adb("shell", "cmd", "uimode", "night", original_night)
        if original_scale == "null":
            driver.adb("shell", "settings", "delete", "system", "font_scale")
        else:
            driver.adb("shell", "settings", "put", "system", "font_scale", original_scale)
        driver.adb("shell", "am", "force-stop", args.package)
    report = {
        "candidate": args.candidate, "api": args.api, "variant": args.variant,
        "apkSha256": apk_hash, "installedApkSha256": installed_hash,
        "status": "captured-pending-human-inspection" if failure is None else "fail",
        "rows": rows, "failure": failure,
        "restored": {"fontScale": original_scale, "night": original_night},
        "limitations": [
            "Only representative initial viewports; not every scroll position or modal state.",
            "No automated claim about clipping, contrast, accessibility, or visual equality.",
            "Synthetic offline fixtures; no Chinese IME or physical-device coverage.",
        ],
    }
    (Path(args.output_dir) / f"{driver.prefix}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({"api": args.api, "status": report["status"], "failure": failure}))
    return 0 if failure is None else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--api", required=True, type=int, choices=(31, 32, 33, 37))
    parser.add_argument("--candidate", default="B02-candidate-3")
    parser.add_argument("--apk", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--variant", required=True, choices=("debug", "release"))
    parser.add_argument("--output-dir", required=True)
    raise SystemExit(capture(parser.parse_args()))
