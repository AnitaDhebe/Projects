
import os
import tempfile
import shutil
import subprocess
import xml.etree.ElementTree as ET

from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import tempfile
from .utils import rerun_handler
from .utils.rerun_handler import rerun_failed_tests
from .forms import UploadXMLForm
from .utils.analyze_xml import analyze_xml
from django.http import FileResponse
from django.http import FileResponse, HttpResponseNotFound

# Paths
XML_REPORT_PATH = os.path.join(settings.MEDIA_ROOT, 'test_results.xml')
RERUN_XML_PATH = os.path.join(settings.MEDIA_ROOT, 'rerun_result.xml')

# ────────────────────────────────────────────────
# 🔹 Upload XML Report
# ────────────────────────────────────────────────
def upload_view(request):
    if request.method == 'POST':
        xml_file = request.FILES.get('xml_file')
        base_folder = request.POST.get('base_folder')

        if not xml_file or not base_folder:
            messages.error(request, "Please provide both XML file and base folder path.")
            return render(request, 'xml_analyzer/upload.html')

        if not os.path.exists(base_folder):
            messages.error(request, "Base folder path does not exist.")
            return render(request, 'xml_analyzer/upload.html')

        fs = FileSystemStorage()
        target_filename = "uploaded_report.xml"

        # Delete old report if exists
        if fs.exists(target_filename):
            fs.delete(target_filename)

        filename = fs.save(target_filename, xml_file)
        file_path = fs.path(filename)

        # Analyze XML
        result_data = analyze_xml(file_path)

        # Save to session
        request.session['result_data'] = result_data
        request.session['base_folder'] = base_folder
        request.session['test_cases'] = (
            result_data.get('passed', []) +
            result_data.get('failed', []) +
            result_data.get('skipped', []) +
            result_data.get('error', [])
        )

        return redirect('results_summary')

    return render(request, 'xml_analyzer/upload.html')

# ────────────────────────────────────────────────
# 🔹 Upload with Test File (Optional)
# ────────────────────────────────────────────────
def upload_report(request):
    if request.method == 'POST':
        form = UploadXMLForm(request.POST, request.FILES)
        if form.is_valid():
            test_case_file = request.FILES['test_case_file']
            xml_file = request.FILES['xml_file']

            temp_dir = tempfile.mkdtemp()
            try:
                test_case_path = os.path.join(temp_dir, test_case_file.name)
                xml_file_path = os.path.join(temp_dir, xml_file.name)

                for f, path in [(test_case_file, test_case_path), (xml_file, xml_file_path)]:
                    with open(path, 'wb+') as dest:
                        for chunk in f.chunks():
                            dest.write(chunk)

                analysis_result = analyze_xml(xml_file_path)
                request.session['result_data'] = analysis_result
                request.session['test_cases'] = (
                analysis_result.get('passed', []) +
                analysis_result.get('failed', []) +
                analysis_result.get('skipped', []) +
                analysis_result.get('error', [])
            )
                if not analysis_result:
                    messages.warning(request, "No results found in the XML file.")
                    return render(request, 'xml_analyzer/upload.html', {'form': form})

                messages.success(request, "Analysis completed successfully.")
                return render(request, 'xml_analyzer/upload.html', {
                    'form': form,
                    'analysis_result': analysis_result,
                })

            finally:
                shutil.rmtree(temp_dir)
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = UploadXMLForm()
    return render(request, 'xml_analyzer/upload.html', {'form': form})

# ────────────────────────────────────────────────
# 🔹 Result Views
# ────────────────────────────────────────────────
def get_result_data(request):
    return request.session.get("result_data", {})

def results_summary_view(request):
    result_data = get_result_data(request)
    if not result_data:
        return redirect("upload")

    # Calculate counts
    passed_count = len(result_data.get('passed', []))
    failed_count = len(result_data.get('failed', []))
    skipped_count = len(result_data.get('skipped', []))
    error_count = len(result_data.get('error', []))
    rerun_passed_count = len(result_data.get('rerun_passed', []))

    total_count = passed_count + failed_count + skipped_count + error_count

    context = {
        "total": total_count,
        "passed": passed_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "error": error_count,
        "rerun_passed": rerun_passed_count
    }

    return render(request, "xml_analyzer/results_summary.html", context)

def results_status_view(request, status):
    test_cases = request.session.get("test_cases", [])
    status = status.lower()

    if status == "total":
        filtered_cases = test_cases  # ← return all test cases
    else:
        filtered_cases = [tc for tc in test_cases if tc["status"].lower() == status]

    context = {
        "test_cases": filtered_cases,
        "status": status.lower()
    }
    return render(request, "xml_analyzer/results_by_status.html", context)

# ────────────────────────────────────────────────
# 🔹 Load & Save XML Helpers
# ────────────────────────────────────────────────
def load_tests_from_xml():
    tests = []
    try:
        tree = ET.parse(XML_REPORT_PATH)
        root = tree.getroot()
        for testcase in root.iter('testcase'):
            name = testcase.get('name')
            classname = testcase.get('classname')
            if testcase.find('failure') is not None:
                status = 'Fail'
            elif testcase.find('error') is not None:
                status = 'Error'
            elif testcase.find('skipped') is not None:
                status = 'Skipped'
            else:
                status = 'Pass'
            tests.append({'name': name, 'classname': classname, 'status': status, 'element': testcase})
        return tree, tests
    except Exception as e:
        print(f"Error loading XML: {e}")
        return None, []

def save_tests_to_xml(tree):
    tree.write(XML_REPORT_PATH)

# ────────────────────────────────────────────────
# 🔹 Rerun Logic
# ────────────────────────────────────────────────

def rerun_view(request):
    # Get paths from session
    uploaded_report_path = request.session.get("uploaded_xml_path")
    test_base_folder = request.session.get("test_base_folder")

    # Fallback if missing or invalid
    if not uploaded_report_path or not os.path.exists(uploaded_report_path):
        context = {"result": {"error": "Uploaded XML report not found. Please upload first."}}
        return render(request, "xml_analyzer/rerun_page.html", context)

    if not test_base_folder or not os.path.exists(test_base_folder):
        # fallback finder function, same as your standalone script
        def find_project_root(start_path, marker="libs"):
            current = os.path.abspath(start_path)
            while current != os.path.dirname(current):
                if os.path.exists(os.path.join(current, marker)):
                    return current
                current = os.path.dirname(current)
            return start_path
        test_base_folder = find_project_root(settings.BASE_DIR)

    # Now call your existing rerun logic function, passing uploaded_report_path and test_base_folder
    # Example (assuming rerun_failed_tests is your function):
    result = rerun_failed_tests(uploaded_report_path, test_base_folder)

    return render(request, "xml_analyzer/rerun_page.html", {"result": result})

def download_final_report(request):
    final_xml_path = os.path.abspath("final_report.xml")
    if os.path.exists(final_xml_path):
        return FileResponse(open(final_xml_path, "rb"), as_attachment=True, filename="final_report.xml")
    return HttpResponseNotFound("Updated XML report not found.")

def failed_tests_view(request):
    result_data = get_result_data(request)
    failed = result_data.get("failed", [])
    return render(request, "xml_analyzer/failed.html", {"testcases": failed})

def skipped_tests_view(request):
    result_data = get_result_data(request)
    skipped = result_data.get("skipped", [])
    return render(request, "xml_analyzer/skipped.html", {"testcases": skipped})

def error_tests_view(request):
    result_data = get_result_data(request)
    error = result_data.get("error", [])
    return render(request, "xml_analyzer/error.html", {"testcases": error})

def rerun_passed_view(request):
    result_data = get_result_data(request)
    rerun = result_data.get("rerun_passed", [])
    return render(request, "xml_analyzer/rerun_passed.html", {"testcases": rerun})

def rerun_page(request):
    """
    Shows rerun page with a button to start rerun.
    On POST, performs rerun and displays summary + download button.
    """
    context = {}

    # Paths from session or config — adjust as needed
    base_folder = request.session.get("base_folder")  # make sure you set this on upload
    xml_path = os.path.join(settings.MEDIA_ROOT, "uploaded_report.xml")

    if request.method == "POST":
        if not base_folder or not os.path.exists(base_folder):
            context["error"] = "Base folder path not found or invalid."
        elif not os.path.exists(xml_path):
            context["error"] = "Uploaded XML report not found."
        else:
            # Call the rerun logic
            result = rerun_failed_tests(xml_path, base_folder)
            context["result"] = result

    return render(request, "xml_analyzer/rerun_page.html", context)

# ────────────────────────────────────────────────
# 🔹 Dashboard (Optional)
# ────────────────────────────────────────────────
def dashboard(request):
    _, tests = load_tests_from_xml()
    context = {
        'tests': tests,
        'passed': [t for t in tests if t['status'] == 'Pass'],
        'failed': [t for t in tests if t['status'] == 'Fail'],
        'skipped': [t for t in tests if t['status'] == 'Skipped'],
        'error': [t for t in tests if t['status'] == 'Error'],
    }
    return render(request, 'xml_analyzer/dashboard.html', context)







