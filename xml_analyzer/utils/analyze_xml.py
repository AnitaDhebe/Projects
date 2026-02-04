import xml.etree.ElementTree as ET

def analyze_xml(file_path):
    result_data = {
        'passed': [],
        'failed': [],
        'skipped': [],
        'error': []
    }

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError:
        print("[XML Analysis] Parse error: Unable to parse the XML file.")
        return result_data
    except Exception as e:
        print(f"[XML Analysis] Unexpected error: {e}")
        return result_data

    for testcase in root.iter('testcase'):
        name = testcase.attrib.get('name')
        classname = testcase.attrib.get('classname', 'Unknown')

        if testcase.find('failure') is not None:
            status = 'failed'
        elif testcase.find('skipped') is not None:
            status = 'skipped'
        elif testcase.find('error') is not None:
            status = 'error'
        else:
            status = 'passed'

        test_entry = {
            'name': name,
            'classname': classname,
            'status': status
        }

        result_data[status].append(test_entry)

    return result_data

