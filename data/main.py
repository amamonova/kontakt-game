import xml
import csv
import requests
from bs4 import BeautifulSoup
import os
import sys
import bz2
import subprocess
from keras.utils import get_file
import re
import wiki_xml_handler
import wiki_code_parser
import data_writer
from timeit import default_timer as timer
from multiprocessing import Pool
import tqdm

# List of lists to single list
from itertools import chain

# Sending keyword arguments in map
from functools import partial


def bytes_to_unicode(bytes):
    return bytes.decode('utf8').replace(u'\xa0', u' ')


def validate_file(filename, is_full):
    multistream = re.findall('multistream', filename)
    if is_full:
        article = re.findall('pages-articles', filename)
    else:
        article = re.findall('pages-articles[1-9]', filename)
    if not multistream and article:
        return True
    return False


def get_file_urls(base_url, version, download_full=False):
    dump_url = base_url + version

    dump_html = requests.get(dump_url).text

    soup_dump = BeautifulSoup(dump_html, 'html.parser')

    files = []
    for file in soup_dump.find_all('li', {'class': 'file'}):
        text = file.text
        if validate_file(text, download_full):
            files.append(text.split()[0])
    return files


def download_files(files, target_dir, url):
    data_paths = []
    for file in files:
        path = target_dir + file
        if not os.path.exists(path):
            data_paths.append(get_file(file, url + file))  # TODO: Add Exceptions
        else:
            data_paths.append(path)
    return data_paths


def parse_dumped_file(input_file, output_file, is_wikipedia=True):
    lines = []
    start = timer()
    handler = wiki_xml_handler.WikiXmlHandler()
    xml_parser = xml.sax.make_parser()
    xml_parser.setContentHandler(handler)
    writer = data_writer.DataWriter(output_file)
    parser = wiki_code_parser.WikiCodeParser(is_wikipedia)
    counter = 0
    for i, line in enumerate(subprocess.Popen(['bzcat'],
                                              stdin=open(input_file),
                                              stdout=subprocess.PIPE).stdout):
        xml_parser.feed(bytes_to_unicode(line))

        if handler.new_page:
            data = handler.read_page()
            try:
                parser.feed(data[0], data[1])
            except IndexError:
                continue
            data = parser.get_data()
            parser.clear()
            writer.write(data, is_wikipedia)
    end = timer()


if __name__ == '__main__':
    print("Do you want to download wikipedia-(1) or wiktionaty-(2)? (1/2)")
    x = int(input())
    if x == 1:
        # wiki
        base_url = 'https://dumps.wikimedia.org/ruwiki/'
        download_full = False
        is_wiki = True
        file_csv_name = 'wikipedia_data'
    else:
        # wikt
        base_url = 'https://dumps.wikimedia.org/ruwiktionary/'
        download_full = True
        is_wiki = False
        file_csv_name = 'wiktionary_data'
    version = '20191001/'
    # recommended keras path: '/home/<username>/.keras/datasets/'
    # WARNING: LINUX OS PATH
    keras_home = input("Input directory path, where you want to store dumped wiki-files\n")
    file_urls = get_file_urls(base_url, version, download_full=download_full)
    file_paths = download_files(file_urls, keras_home, base_url + version)
    pool = Pool(processes=4)
    task_args = [(file, file_csv_name + str(i) + '.csv', True) for i, file in enumerate(file_paths)]

    results = pool.starmap(parse_dumped_file, task_args)

    pool.close()
    pool.join()
