import xml
import os
import requests
import subprocess
import re

from bs4 import BeautifulSoup
from keras.utils import get_file
from multiprocessing import Pool

import wiki_xml_handler
import wiki_code_parser
import data_writer

# List of lists to single list
from itertools import chain

# Sending keyword arguments in map
from functools import partial

multistream_reg = re.compile('multistream')
pages_full_reg = re.compile('pages-articles')
pages_reg = re.compile('pages-articles[1-9]')


def bytes_to_unicode(bytes):
    return bytes.decode('utf8').replace(u'\xa0', u' ')


def validate_file(filename, is_full):
    """We should only download files with pages-articles substing in name"""
    multistream = multistream_reg.findall(filename)
    article_pattern = pages_full_reg if is_full else pages_reg
    article = article_pattern.findall(filename)
    if not multistream and article:
        return True
    return False


def get_file_urls(base_url, version, download_full=False):
    """Parse file urls from wiki dump page"""
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
    """Download files by URLS, function get_file use TensorFlow"""
    data_paths = []
    for file in files:
        path = target_dir + file
        if not os.path.exists(path):
            data_paths.append(get_file(file, url + file))  # TODO: Add Exceptions
        else:
            data_paths.append(path)
    return data_paths


def parse_dumped_file(input_file, output_file, is_wikipedia):
    handler = wiki_xml_handler.WikiXmlHandler()
    xml_parser = xml.sax.make_parser()
    xml_parser.setContentHandler(handler)
    writer = data_writer.DataWriter(output_file)
    wiki_parser = wiki_code_parser.WikiCodeParser(is_wikipedia)
    # bzcat = console utility, read .bz compressed file line by line
    for i, line in enumerate(subprocess.Popen(['bzcat'],
                                              stdin=open(input_file),
                                              stdout=subprocess.PIPE).stdout):
        # Parse XML file line by line, return data to handler data[0] - page title, data[1] - page data
        xml_parser.feed(bytes_to_unicode(line))

        # If handler gets signal, that xml_parser read new page:
        if handler.new_page:
            # 1) Get this data
            data = handler.read_page()
            try:
                # 2) Load it to parser of wiki code
                wiki_parser.feed(data[0], data[1])
            except IndexError:
                continue
            # 3) Get data from wiki code parser
            data = wiki_parser.get_data()
            wiki_parser.clear()
            # 4) Write it to csv file
            writer.write(data, is_wikipedia)


if __name__ == '__main__':
    print("Do you want to download wikipedia-(1) or wiktionaty-(2)? (1/2)")
    x = int(input())

    base_url = 'https://dumps.wikimedia.org/ruwiki/' if x == 1 else 'https://dumps.wikimedia.org/ruwiktionary/'
    download_full = x != 1
    is_wiki = x == 1
    file_csv_name = 'wikipedia_data' if x == 1 else 'wiktionary_data'

    version = '20191001/'
    # recommended keras path: '/home/<username>/.keras/datasets/'
    # WARNING: LINUX OS PATH
    keras_home = input("Input directory path, where you want to store dumped wiki-files\n")
    file_urls = get_file_urls(base_url, version, download_full=download_full)
    file_paths = download_files(file_urls, keras_home, base_url + version)
    # Creating 4 processes, If you have other amount of CPUCores, you can change this
    pool = Pool(processes=4)
    task_args = [(file, file_csv_name + str(i) + '.csv', is_wiki) for i, file in enumerate(file_paths)]
    # Every process will run parse_dumped_file function
    results = pool.starmap(parse_dumped_file, task_args)

    pool.close()
    pool.join()
