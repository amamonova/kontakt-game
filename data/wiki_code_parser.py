import re

import gensim as gensim
import mwparserfromhell

PHRASEME_SEP = '[*#]'

RELATION_SEP = '[*#,]'

re_quotation = re.compile('[\'\"]')
re_html_tags = re.compile('<.*?>')
re_validate_text = re.compile('#REDIRECT')
re_template_wiki = re.compile('{{выдел|}}')
re_wiki_separator = re.compile('\|')
re_wiki_braces = re.compile('[{}]')


def _clean_text_from_quotation(text):
    return re_quotation.sub('', text)


# TODO: Add to utils
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    return (l[i:i + n] for i in range(0, len(l), n))


def _remove_html_tags(text):
    """Remove html tags from a string"""
    return re_html_tags.sub('', text)


def _trim_string(string):
    """"Remove extra spaces, remove trailing spaces"""
    return re.sub('\s+', ' ', string).strip()


# This function works only with russian words!
def _remove_accents(string):
    bytes = string.encode('utf-8')
    bytes = bytes.replace(b'\xcc\x81', b'')
    return bytes.decode('utf-8')


def clean_string(string,
                 min_len=2,
                 max_len=30):
    string = re.compile("\"").sub('', string)
    string = re.compile("\\\\").sub(' ', string)  # Important for csv delimiter correctness
    string = _remove_html_tags(string)
    string = _remove_accents(string)
    string = _trim_string(string)
    string = _clean_text_from_quotation(string)
    return string


def clean_wikilist(text, separator):
    items = re.compile(separator).split(text)
    try:
        items.pop(0)
    except IndexError:
        return  # drop first item
    result = []
    for item in items:
        mixed_text = mwparserfromhell.parse(item).strip_code()
        pure_text = clean_string(mixed_text)
        result.append(pure_text)
    return result


def clean_meanings(text):
    items = re.compile('[*#]').split(text)
    try:
        items.pop(0)
    except IndexError:
        return
    result = []
    for item in items:
        templates = mwparserfromhell.parse(item).filter_templates()
        text_meaning = mwparserfromhell.parse(item).strip_code()
        text_meaning = clean_string(text_meaning)
        meaning = (text_meaning, [])
        for template in templates:
            if template.name.lower() == 'пример':
                try:
                    example = template.params[0]

                    # TODO: Make separate function to parse example

                    example = mwparserfromhell.parse(example).strip_code()

                    # Remove {{выдел|word}} pattern

                    example = re_template_wiki.sub(' ', example)
                    example = re_wiki_separator.sub('', example)
                    example = re_wiki_braces.sub('', example)

                    example = clean_string(example)

                    meaning[1].append(example)
                except IndexError:
                    continue
        result.append(meaning)
    return result


def validate_title(title):
    if re.findall(':', title):
        return False
    return re.match(r"[а-яА-ЯёЁ\s]+", title)


def validate_text(text):
    not_redirect = re_validate_text.findall(text) == []
    rus_page = re.findall('{{-ru-}}', text) != []
    return not_redirect and rus_page


class WiktionaryParser:
    def __init__(self):
        self._part_of_speech = ""
        self._relations = {
            'synonyms': [],
            'antonyms': [],
            'hypernyms': [],
            'hyponyms': []
        }
        self._meanings = []
        self._phraseme = []
        self.re_relations_dict = {
            'synonyms': re.compile('синонимы'),
            'antonyms': re.compile('антонимы'),
            'hypernyms': re.compile('гиперонимы'),
            'hyponyms': re.compile('гипонимы')
        }

    def parse(self, text):
        splited_text = text.split('===')
        splited_text.pop(0)  # Drop special tag
        chunked_list = list(chunks(splited_text, 2))

        for item in chunked_list:
            try:
                title, text = item
            except ValueError:
                continue
            lower_title = title.lower()
            lower_text = text.lower()
            if not self._meanings and re.search('значение', lower_title):
                self._meanings = clean_meanings(text)
            for relation, pattern in self.re_relations_dict.items():
                if not self._relations[relation] and pattern.search(lower_title):
                    self._relations[relation] = clean_wikilist(text, separator=RELATION_SEP)
            if not self._phraseme and re.search('фразеологизмы', lower_title):
                text = re.sub('частичн', '', lower_text)
                self._phraseme = clean_wikilist(text, separator=PHRASEME_SEP)
            if not self._part_of_speech and re.search('морфологические и синтаксические свойства', lower_title):
                if re.search('сущ', lower_text):
                    self._part_of_speech = 'noun'
                else:
                    self._part_of_speech = 'other'

        return []

    def get_data(self):
        return {'part of speech': self._part_of_speech,
                'meanings': self._meanings,
                'relations': self._relations,
                'phraseme': self._phraseme}


class WikiPediaParser:
    def __init__(self):
        self._text = ''

    def parse(self, text):
        text = mwparserfromhell.parse(text).strip_code()  # Remove WikiCode {{}}, [[]]
        clean = re.compile('==[ а-яА-Я]*==')  # Remove == SubTitle ==
        text = re.sub(clean, ' ', text)
        text = re.sub('Категория:', '', text)  # Remove wiki additional tags
        text = clean_string(text)
        self._text = text

    def get_data(self):
        return {'text': self._text}


class WikiCodeParser:
    def __init__(self, is_wikipedia):
        self._title = ""
        self._text = ""
        self._is_wiki = is_wikipedia
        self._page_data = {}

    def clear(self):
        self._title = ""
        self._text = ""
        self._page_data = {}

    def feed(self, title, text):
        self.clear()
        if not validate_title(title) or not validate_text(text):
            return
        self._title = title
        self._text = text
        if self._is_wiki:
            wiki_pedia_parser = WikiPediaParser()
            wiki_pedia_parser.parse(text)
            self._page_data = wiki_pedia_parser.get_data()
        else:
            wiktionary_parser = WiktionaryParser()
            wiktionary_parser.parse(text)
            self._page_data = wiktionary_parser.get_data()

    def get_data(self):
        if not self._page_data:
            return '', {}
        return self._title, self._page_data
