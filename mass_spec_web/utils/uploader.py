import json
import os
import sys
from io import BytesIO

# os.environ['DJANGO_SETTINGS_MODULE'] = 'mass_spec_project.settings'
#
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#
# import django
# django.setup()


class UploadSpectrum(object):
    def __init__(self, data):
        data = data
        self.uploaded_file = data.get('file')
        self.parsing()

    def parsing(self):
        uploaded_file = self.uploaded_file
        filename = BytesIO(uploaded_file.read())
        spectrum_dict = {}
        for i in filename:
            item = i.decode('utf8').replace("'", '"').split(':')
            d = {item[0]: item[1].rsplit()}
            spectrum_dict.update(d)

        s = json.dumps(spectrum_dict, indent=4, sort_keys=True)

        print('dict', s)
        print('type', type(s))
        return spectrum_dict
