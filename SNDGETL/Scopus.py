import json
import requests
import logging

from SNDGETL import init_log, ProcessingException

_log = logging.getLogger(__name__)






class Scopus:
    DEFAULT_ENDPOINT = "https://api.elsevier.com/content/search/scopus"

    def __init__(self, apikey):
        self.apikey = apikey

    def doi(self, doi):

        requests.get(f'{self.endpoint}?query=PMID({doi})&apiKey={self.apikey}&view=COMPLETE')