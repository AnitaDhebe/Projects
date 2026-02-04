# forms.py
from django import forms

class UploadXMLForm(forms.Form):
    test_case_file = forms.FileField(label="Python Test Cases File")
    xml_file = forms.FileField(label='Upload XML Report For Same Test Cases File')
