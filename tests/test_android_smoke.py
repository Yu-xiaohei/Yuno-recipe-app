"""Reusable B02 device checks, invoked explicitly (no device work during unittest discovery).

Runs only against the isolated prototype package. Evidence is retained under --output-dir.
Requires an already booted, task-owned emulator; physical devices need a separate review.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET


class AndroidSmoke:
    def __init__(self, args):
        self.args = args
        self.output = Path(args.output_dir)
        self.output.mkdir(parents=True, exist_ok=True)
        self.prefix = f"test_b02_api{args.api}_{args.variant}"
        self.results = []
        self.ui_retries = []
        self.last_ui_dump_output = None
        self.remote_xml = f"/data/local/tmp/tmp_b02_smoke_{time.strftime('%Y%m%d_%H%M%S')}.xml"

    def adb(self, *parts, binary=False):
        result = subprocess.run(
            [self.args.adb, "-s", self.args.serial, *parts],
            capture_output=True, timeout=60, check=True,
        )
        return result.stdout if binary else result.stdout.decode("utf-8", errors="replace").strip()

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)
        self.results.append(message)

    def ui(self):
        for attempt in range(3):
            try:
                self.last_ui_dump_output = self.adb(
                    "shell", "uiautomator", "dump", "--compressed", self.remote_xml,
                )
                raw = self.adb("shell", "cat", self.remote_xml)
                return ET.fromstring(raw)
            except subprocess.CalledProcessError as error:
                diagnostic = (error.stdout + error.stderr).decode("utf-8", errors="replace")
                transient = any(message in diagnostic.lower() for message in (
                    "could not get idle state", "null root node returned",
                ))
                if not transient or attempt == 2:
                    raise
                self.ui_retries.append(diagnostic.strip())
                time.sleep(0.5)

    def wait_node(self, resource_id, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            tree = self.ui()
            for node in tree.iter("node"):
                if node.get("resource-id") == resource_id:
                    return node
            time.sleep(0.3)
        raise AssertionError(f"Missing visible node: {resource_id}")

    @staticmethod
    def bounds(node):
        numbers = list(map(int, re.findall(r"\d+", node.attrib["bounds"])))
        if len(numbers) != 4 or numbers[2] <= numbers[0] or numbers[3] <= numbers[1]:
            raise AssertionError(f"Unusable bounds: {node.attrib}")
        return numbers

    def tap(self, resource_id):
        node = self.wait_node(resource_id)
        left, top, right, bottom = self.bounds(node)
        self.adb("shell", "input", "tap", str((left + right) // 2), str((top + bottom) // 2))
        time.sleep(0.4)
        return node

    def scroll_to(self, resource_id):
        """Find a control in the settings scroll area without swiping the floating navigation."""
        for _ in range(12):
            for node in self.ui().iter("node"):
                if node.get("resource-id") == resource_id:
                    left, top, right, bottom = self.bounds(node)
                    if bottom < 2100 and top > 80:
                        return node
            self.adb("shell", "input", "swipe", "540", "1700", "540", "650", "400")
        raise AssertionError(f"Control not reachable by settings scroll: {resource_id}")

    def screenshot(self, suffix):
        destination = self.output / f"{self.prefix}_{suffix}.png"
        destination.write_bytes(self.adb("exec-out", "screencap", "-p", binary=True))

    def logs(self):
        pid = self.adb("shell", "pidof", self.args.package)
        self.require(bool(pid), "prototype process remains alive")
        return self.adb("logcat", "-d", f"--pid={pid.split()[0]}", "-s", "YunoB02:I", "AndroidRuntime:E")

    def launch(self, fault=None):
        self.adb("shell", "am", "force-stop", self.args.package)
        command = ["shell", "am", "start", "-W", "-n",
                   f"{self.args.package}/com.yunobase.recipe.MainActivity"]
        if fault:
            command += ["--ez", f"b02.force_{fault}_failure", "true"]
        result = self.adb(*command)
        if "Status: ok" not in result:
            raise AssertionError(f"cold activity start did not return Status: ok; output={result!r}")
        self.require("Status: ok" in result, "cold activity start returns Status: ok")
        self.wait_node("b02_recipe_0")
        self.wait_node("b02_material_surface")

    def run(self):
        self.require(self.args.serial.startswith("emulator-"), "target is an emulator")
        self.require(self.args.package in (
            "com.yunobase.recipe.prototype",
            "com.yunobase.recipe.prototype.debug",
        ), "only the isolated prototype package is allowed")
        api = self.adb("shell", "getprop", "ro.build.version.sdk")
        self.require(api == str(self.args.api), f"device SDK equals {self.args.api}")
        self.require(self.adb("shell", "getprop", "sys.boot_completed") == "1", "device boot completed")
        install = self.adb("install", "-r", str(Path(self.args.apk).resolve()))
        self.require("Success" in install, "APK installs successfully")
        installed = self.adb("shell", "pm", "path", self.args.package).splitlines()
        self.require(len(installed) == 1 and installed[0].startswith("package:") and
                     self.adb("shell", "sha256sum", installed[0].removeprefix("package:")).split()[0] ==
                     hashlib.sha256(Path(self.args.apk).read_bytes()).hexdigest(),
                     "installed APK bytes match the tested artifact")
        self.launch()
        initial = self.ui()
        texts = {node.get("text") for node in initial.iter("node")}
        self.require({"配餐", "食谱", "设置"}.issubset(texts), "all three existing tab labels are visible")
        self.wait_node("b02_brand_header")
        self.wait_node("b02_filter_0")
        self.wait_node("b02_filter_1")
        self.require({"全部重量", "全部热量", "全部分类", "西红柿炒鸡蛋"}.issubset(texts),
                     "Figma home structure and representative recipe are present")
        initial_logs = self.logs()
        expected_material = "enhanced" if self.args.api >= 33 else "clear"
        self.require(f"material={expected_material}" in initial_logs, f"expected material branch is {expected_material}")
        self.require("font=MiSans-VF-4.009" in initial_logs, "MiSans font build is running")
        decoded = re.findall(r"thumbnail-decoded; width=(\d+); height=(\d+)", initial_logs)
        self.require(bool(decoded) and all(max(map(int, size)) <= 512 for size in decoded),
                     "thumbnail decoding stays bounded instead of decoding full-resolution originals")
        self.require("asset-error" not in initial_logs, "local SVG and thumbnail loading has no reported error")
        if self.args.api >= 33:
            self.require("glass-pipeline; refraction=true" in initial_logs,
                         "real effect pipeline initializes refraction; pixel appearance checked separately")
            self.require("effect-failed" not in initial_logs and "fallback=clear" not in initial_logs
                         and "material=clear" not in initial_logs,
                         "normal enhanced launch does not silently fall back")
        self.screenshot("home")
        self.adb("shell", "input", "swipe", "540", "1850", "540", "700", "500")
        self.wait_node("b02_material_surface")
        self.screenshot("scrolled")
        scroll_logs = self.logs()
        self.require("FATAL EXCEPTION" not in scroll_logs, "scrolling does not crash")
        if self.args.api == 33:
            self.require("effect-failed" not in scroll_logs and "material=clear" not in scroll_logs,
                         "enhanced scrolling does not silently fall back")

        for index, opening, menu, option in (
            (0, "b02_filter_0", "b02_filter_menu_0", "100~200 g"),
            (1, "b02_filter_1", "b02_filter_menu_1", "100~200 Kcal"),
            (2, "b02_menu_open", "b02_category_menu", "热菜"),
        ):
            self.tap(opening)
            self.wait_node(menu)
            self.require(any(node.get("text") == option for node in self.ui().iter("node")),
                         f"filter {index} opens its actual Miuix option list")
            if index == 2:
                for _ in range(4):
                    if any(node.get("text") == "食材" for node in self.ui().iter("node")):
                        break
                    popup = self.wait_node(menu)
                    scroll = next(node for node in popup.iter("node")
                                  if node.get("scrollable") == "true")
                    left, top, right, bottom = self.bounds(scroll)
                    center = str((left + right) // 2)
                    inset = max(20, (bottom - top) // 6)
                    self.adb("shell", "input", "swipe", center, str(bottom - inset),
                             center, str(top + inset), "400")
                self.require(any(node.get("text") == "食材" for node in self.ui().iter("node")),
                             "ingredient category remains reachable by actual popup scrolling")
            self.screenshot(f"menu_{index}")
            self.adb("shell", "input", "keyevent", "4")
            self.require(not any(node.get("resource-id") == menu for node in self.ui().iter("node")),
                         f"back dismisses filter {index}")
        self.tap("b02_tab_0")
        self.wait_node("b02_meal_overview")
        self.screenshot("meals")
        self.tap("b02_meal_open")
        before = self.wait_node("b02_weight_value").get("text", "")
        slider = self.wait_node("b02_weight_slider")
        left, top, right, bottom = self.bounds(slider)
        self.adb("shell", "input", "swipe", str((left + right) // 2), str((top + bottom) // 2),
                 str(right - 2), str((top + bottom) // 2), "500")
        after = self.wait_node("b02_weight_value").get("text", "")
        self.require(before != after, "slider changes the displayed aggregate weight")
        self.tap("b02_lock_switch")
        self.require(self.wait_node("b02_weight_slider").get("enabled") == "false",
                     "lock disables weight interaction")
        self.adb("shell", "input", "swipe", str(right - 2), str((top + bottom) // 2),
                 str(left + 2), str((top + bottom) // 2), "500")
        self.require(self.wait_node("b02_weight_value").get("text", "") == after,
                     "locked slider gesture does not alter weight")
        self.screenshot("weight_locked")

        self.tap("b02_detail_back")
        self.tap("b02_tab_1")
        # A list may retain its scroll position, so choose any currently visible fixture.
        candidates = [node for node in self.ui().iter("node")
                      if re.fullmatch(r"b02_recipe_\d+", node.get("resource-id", ""))]
        self.require(bool(candidates), "scrolled list retains visible fixture cards")
        self.tap(candidates[0].get("resource-id"))
        self.wait_node("b02_dialog_confirm")
        self.screenshot("dialog")
        self.tap("b02_dialog_confirm")

        self.tap("b02_search_input")
        self.wait_node("b02_search_close")
        self.adb("shell", "input", "text", "ab")
        self.wait_node("b02_search_submit")
        self.screenshot("keyboard")
        self.tap("b02_search_submit")
        self.require("fixture-search-submitted" not in self.logs(),
                     "uncommitted Latin IME composition does not submit a query")
        # AOSP LatinIME also composes ASCII words. Space commits that word; trim keeps "ab".
        self.adb("shell", "input", "text", "%s")
        self.tap("b02_search_submit")
        self.require("fixture-search-submitted; composition=false" in self.logs(),
                     "explicit committed search submits the fixture query")
        self.adb("shell", "input", "keyevent", "4")
        self.wait_node("b02_tab_2")
        self.require(not any(node.get("resource-id") == "b02_search_close"
                             for node in self.ui().iter("node")),
                     "back closes expanded search and restores navigation")
        self.tap("b02_search_input")
        self.tap("b02_search_close")
        self.wait_node("b02_tab_2")
        self.require(not any(node.get("resource-id") == "b02_search_close"
                             for node in self.ui().iter("node")),
                     "explicit cancel closes expanded search and restores navigation")
        self.tap("b02_tab_2")
        self.screenshot("settings")
        self.scroll_to("b02_licenses_open")
        self.tap("b02_licenses_open")
        self.require(self.wait_node("b02_font_attribution").get("text") == "本应用使用 MiSans 字体",
                     "approved MiSans attribution is visible from settings")
        self.screenshot("licenses")
        self.tap("b02_detail_back")
        self.scroll_to("b02_reduce_motion")
        self.tap("b02_reduce_motion")
        self.tap("b02_tab_1")
        self.wait_node("b02_material_surface")
        self.require("material=clear" in self.logs(), "reduced motion retains a readable clear branch")

        for failure_stage in ("effect", "draw") if self.args.api >= 33 else ():
            self.launch(fault=failure_stage)
            # The failed effect schedules a safe recomposition to clear material.
            deadline = time.monotonic() + 10
            fault_logs = ""
            while time.monotonic() < deadline:
                fault_logs = self.logs()
                if "effect-failed; fallback=clear" in fault_logs and "material=clear" in fault_logs:
                    break
                time.sleep(0.3)
            self.require("effect-failed; fallback=clear" in fault_logs and "material=clear" in fault_logs,
                         f"actual {failure_stage} failure boundary falls back without crashing")
            self.screenshot(f"{failure_stage}_fault_fallback")
        self.require("FATAL EXCEPTION" not in self.logs(), "no fatal exception in the prototype process")

    def execute(self):
        status = "pass"
        failure = None
        failure_details = None
        try:
            self.run()
        except Exception as error:
            status = "fail"
            failure = f"{type(error).__name__}: {error}"
            if isinstance(error, subprocess.CalledProcessError):
                failure_details = {
                    "returnCode": error.returncode,
                    "stdout": (error.stdout or b"").decode("utf-8", errors="replace"),
                    "stderr": (error.stderr or b"").decode("utf-8", errors="replace"),
                    "lastUiDumpOutput": self.last_ui_dump_output,
                }
        report = {
            "candidate": getattr(self.args, "candidate", "B02-candidate-3"),
            "status": status, "serial": self.args.serial, "api": self.args.api,
            "variant": self.args.variant, "package": self.args.package,
            "apkSha256": hashlib.sha256(Path(self.args.apk).read_bytes()).hexdigest(),
            "checks": self.results, "failure": failure,
            "failureDetails": failure_details,
            "transientUiDumpRetries": self.ui_retries,
            "limitations": [
                "Synthetic offline prototype, not recipe/meal functionality.",
                "MiSans original VF and license packaged; rare-glyph fallback remains manual.",
                "ASCII keyboard only; Chinese IME composition remains a separate manual check.",
                "No physical vivo device or broad GPU/performance certification.",
            ],
        }
        (self.output / f"{self.prefix}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        print(json.dumps({"status": status, "api": self.args.api, "variant": self.args.variant,
                          "checks": len(self.results), "failure": failure}, ensure_ascii=False))
        return 0 if status == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--api", required=True, type=int, choices=(31, 32, 33, 37))
    parser.add_argument("--candidate", default="B02-candidate-3")
    parser.add_argument("--apk", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--variant", required=True, choices=("debug", "release"))
    parser.add_argument("--output-dir", required=True)
    return AndroidSmoke(parser.parse_args()).execute()


if __name__ == "__main__":
    raise SystemExit(main())
