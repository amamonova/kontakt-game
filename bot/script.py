from future import standard_library
import gensim
import re
import os
import sys
import wget
from ufal.udpipe import Model, Pipeline
import pandas as pd
import numpy as np
import random
import nltk
from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation


class KontaktModel:
    def __init__(self):
        standard_library.install_aliases()
        nltk.download('stopwords')
        mystem = Mystem()
        russian_stopwords = stopwords.words("russian")

        # colujmns: title
        self.nouns = pd.read_csv('wide_wikt.csv')
        self.local_nouns = None  # TODO: Add locality
        self.model = gensim.models.KeyedVectors.load('araneum_none_fasttextcbow_300_5_2018.model')

    def preprocess_text(self, text):
        tokens = mystem.lemmatize(text.lower())
        tokens = [token for token in tokens if token not in russian_stopwords \
                  and token != " " \
                  and token.strip() not in punctuation]
        return " ".join(tokens)

    def predict_word(self, text, prefix=''):
        words = (self.preprocess_text(text)).split(' ')
        prefix_titles = self.nouns[self.nouns['title'].str.startswith(prefix)]

        if prefix_titles.empty:
            return ""

        stats = prefix_titles['title'].map(lambda x: self.model.n_similarity([x], words))
        df = pd.DataFrame({'title': prefix_titles['title'],
                           'stats': stats})

        return df[df['stats'] == df['stats'].max()]['title'].values[0]

    def get_random_word(self):
        return self.nouns.sample(1)['title'].values[0]

    def close(self):
        del self.model
