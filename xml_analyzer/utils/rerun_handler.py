# xml_analyzer/rerun_handler.py
import os
import sys
import subprocess
import xml.etree.ElementTree as ET

def find_project_root(start_path, marker="libs"):
    current = os.path.abspath(start_path)
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, marker)):
            return current
        current = os.path.dirname(current)
    # fallback: return start_path itself (or raise error)
    return start_path

def parse_failed_tests(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    failed_tests = []
    for testcase in root.iter("testcase"):
        # look for failed tests (failure or error)
        if testcase.find("failure") is not None or testcase.find("error") is not None:
            classname = testcase.attrib.get("classname")
            name = testcase.attrib.get("name")
            if classname and name:
                failed_tests.append((classname, name))
    return failed_tests

def build_pytest_args(base_folder, failed_tests):
    """
    From base_folder and list of (classname, testname),
    build full pytest command line args including file paths and test names.
    """
    pytest_args = []
    missing = []
    print(failed_tests)

    for classname, testname in failed_tests:
        print(classname)
        # Convert classname like 'test_logiclayer.test_output.Test' to file path like
        # base_folder/test_logiclayer/test_output.py
        parts = classname.split(".")
        print(parts)
        # drop the last part if it's a class name? Usually last is class name or module?
        # To be safe, try to locate file using all but last if last starts with uppercase (class),
        # else keep all parts.
        last_part = parts[-1]
        if last_part and last_part[0].isupper():
            # likely a class name, so drop last part to get module path
            module_parts = parts[:-1]
        else:
            module_parts = parts
        # construct file path:
        file_path = os.path.join(base_folder, *module_parts) + ".py"

        print(f"DEBUG: Looking for test file: {file_path}")
        args = f"{file_path}::{testname}"
        pytest_args.append(args)

        print('args::::::::::', f"{file_path}::{testname}")

        missing = False
    return pytest_args, missing

def count_results(xml_path):
    passed = failed = skipped = error = 0
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for testcase in root.iter("testcase"):
        if testcase.find("failure") is not None:
            failed += 1
        elif testcase.find("error") is not None:
            error += 1
        elif testcase.find("skipped") is not None:
            skipped += 1
        else:
            passed += 1
    return passed, failed, error, skipped

import xml.etree.ElementTree as ET

def merge_rerun_results(original_xml, rerun_xml, output_path):
    def parse_test_results(xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        results = {}
        for testcase in root.iter("testcase"):
            name = testcase.attrib.get("name")
            classname = testcase.attrib.get("classname", "")
            status = "passed"
            if testcase.find("failure") is not None:
                status = "failed"
            elif testcase.find("error") is not None:
                status = "error"
            elif testcase.find("skipped") is not None:
                status = "skipped"
            test_id = f"{classname}::{name}".strip(":")
            results[test_id] = (status, testcase)
        return results, tree

    def update_summary_counts(tree):
        root = tree.getroot()

        def update_counts_on_element(elem):
            testcases = elem.findall(".//testcase")
            if not testcases:
                return False
            total = len(testcases)
            failures = sum(1 for tc in testcases if tc.find("failure") is not None)
            errors = sum(1 for tc in testcases if tc.find("error") is not None)
            skipped = sum(1 for tc in testcases if tc.find("skipped") is not None)
            total_time = sum(float(tc.attrib.get("time", 0)) for tc in testcases if "time" in tc.attrib)
            elem.set("tests", str(total))
            elem.set("failures", str(failures))
            elem.set("errors", str(errors))
            elem.set("skipped", str(skipped))
            elem.set("time", f"{total_time:.3f}")
            return True

        updated = False
        if root.tag == "testsuites":
            for ts in root.findall("testsuite"):
                updated |= update_counts_on_element(ts)
        elif root.tag == "sections":
            for section in root.findall("section"):
                updated |= update_counts_on_element(section)
        elif root.tag == "testsuite":
            updated |= update_counts_on_element(root)
        else:
            for elem in root:
                if elem.findall(".//testcase"):
                    updated |= update_counts_on_element(elem)
            if not updated:
                updated |= update_counts_on_element(root)
        return updated

    # Parse both reports
    original_results, original_tree = parse_test_results(original_xml)
    rerun_results, _ = parse_test_results(rerun_xml)
    if original_tree is None or not rerun_results:
        print("Error: failed to parse XMLs or rerun results are empty.")
        return 0

    # Find which failed tests passed on rerun
    passed_after_rerun = []
    for test_id, (status, _) in original_results.items():
        if status in ["failed", "error"]:
            rerun_status, _ = rerun_results.get(test_id, (None, None))
            if rerun_status == "passed":
                passed_after_rerun.append(test_id)
                continue
            # fallback: match just name
            fallback_name = test_id.split("::")[-1]
            for r_id, (r_status, _) in rerun_results.items():
                if r_status == "passed" and r_id.endswith(f"::{fallback_name}"):
                    passed_after_rerun.append(test_id)
                    break

    # Apply changes
    updated_count = 0
    for test_id in passed_after_rerun:
        if test_id in original_results:
            _, test_elem = original_results[test_id]
            for tag in ["failure", "error", "skipped"]:
                for elem in list(test_elem.findall(tag)):
                    test_elem.remove(elem)
            updated_count += 1

    update_summary_counts(original_tree)
    original_tree.write(output_path, encoding="utf-8", xml_declaration=True)

    return updated_count

def find_test_file(module_name, base_folder):
    """Recursively search for a file named <module_name>.py starting from base_folder."""
    for root, _, files in os.walk(base_folder):
        if f"{module_name}.py" in files:
            return os.path.join(root, f"{module_name}.py")
    return None

def rerun_failed_tests(original_xml, base_folder):
    if not os.path.exists(original_xml):
        print(f"❌ Original XML report file not found: {original_xml}")
        sys.exit(1)
    if not os.path.exists(base_folder):
        print(f"❌ Base folder path not found: {base_folder}")
        sys.exit(1)

    root = find_project_root(base_folder, "libs")
    print(f"✅ Found root with 'libs': {root}\n")

    failed_tests = parse_failed_tests(original_xml)
    if not failed_tests:
        print("✅ No failed tests found in the report.")
        sys.exit(0)

    print(f"🔍 Found {len(failed_tests)} failed test(s). Searching test files...\n")
    print(f"DEBUG: failed_tests = {failed_tests}\n")

    pytest_args = []
    missing_tests = []

    for module, test_name in failed_tests:
        test_file = find_test_file(module, base_folder)
        if test_file:
            print(f"✅ Found test file: {test_file}")
            pytest_args.append(f"{test_file}::{test_name}")
        else:
            print(f"❌ Could not find test file for module: {module}")
            missing_tests.append((module, test_name))

    if missing_tests:
        print("\n⚠️ Missing test files for the following test cases:")
        for mod, name in missing_tests:
            print(f" - {mod}::{name}")

    if not pytest_args:
        print("❌ No valid test files found for rerun.")
        sys.exit(1)

    print("\n🔄 Rerunning failed tests...\n")
    pytest_cmd = [
        sys.executable,
        "-m", "pytest",
        "-v",
        "--tb=short",
        "--maxfail=1000",
        "--disable-warnings",
        "--junitxml", "rerun_output.xml"
    ] + pytest_args

    print(" Running command:")
    print(" ".join(pytest_cmd) + "\n")

    subprocess.run(pytest_cmd)

    rerun_xml_path = "rerun_output.xml"
    passed, failed, error, skipped = count_results(rerun_xml_path)
    still_failing = failed + error + skipped

    # Merge rerun results with the original XML
    final_xml = "final_report.xml"
    updated_count = merge_rerun_results(original_xml, rerun_xml_path, final_xml)
    print(f"\n🔄 Merged rerun results into final report. {updated_count} test case(s) updated.")

    return {
        "message": "Rerun complete.",
        "failed_before": len(failed_tests),
        "passed_after_rerun": passed,
        "still_failing": still_failing,
        "failed": failed,
        "error": error,
        "skipped": skipped,
        "updated_xml": final_xml,
    }
