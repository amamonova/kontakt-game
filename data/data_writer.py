import csv
import pandas as pd
import atexit



class DataWriter:
    def __init__(self, file_path):
        self._writed = False
        self._file_open = False
        self._file = None
        self._writer = None
        self._path = file_path
        self._data_frame = None
        self._data_dict = {'title' : [], 'POS': [], 'meanings': [], 'relations': [], 'phraseme': []}

    def _open_file(self):
        self._file_open = True
        self._file = open(self._path, 'w')  # TODO w+?, exceptions!
        self._writer = csv.writer(self._file, delimiter='\\')

    def write(self):
        self._data_frame = pd.DataFrame.from_dict(self._data_dict)
        self._data_frame.to_json(self._file)

    def feed(self, data, is_wikipedia):
        try:
            title, title_data = data[0], data[1]
        except ValueError:
            return
        if not title or not title_data:
            return
        if not self._file_open:
            self._open_file()
        if is_wikipedia:
            self._writer.writerow([title, title_data])
        else:
            try:
                part_of_speech = title_data['part of speech']
                meanings = title_data['meanings']
                relations = title_data['relations']
                phraseme = title_data['phraseme']
            except KeyError:
                return
            self._data_dict['title'].append(title)
            self._data_dict['POS'].append(part_of_speech)
            self._data_dict['meanings'].append(meanings)
            self._data_dict['relations'].append(relations)
            self._data_dict['phraseme'].append(phraseme)