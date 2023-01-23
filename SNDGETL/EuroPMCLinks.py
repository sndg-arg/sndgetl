'''
https://europepmc.org/RestfulWebService#!/Europe32PMC32Articles32RESTful32API/dataLinks

'''

import requests
import logging

from SNDGETL import init_log, ProcessingException

_log = logging.getLogger(__name__)


class EuroPMCLinks:
    DEFAULT_ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{pmcid}/datalinks?format=json"
    DEFAULT_SOURCE = "MED"

    def __init__(self, endpoint=DEFAULT_ENDPOINT):
        self.endpoint = endpoint

    def query(self, source, pmcid):
        result = requests.get(self.endpoint.format(source=source, pmcid=pmcid))
        if result.ok:
            data = result.json()
            if data["hitCount"] > 0:
                return data["dataLinkList"]["Category"]
            else:
                return []

        else:
            ex = ProcessingException("error in http request",
                                     data=[self.endpoint, result.status_code, result.text])
            logging.error("error executing page handler", exc_info=ex)
            raise ex


if __name__ == "__main__":
    import os
    import json
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Gets related datasets from EUPMC article')

    parser.add_argument('pmcid', action='store', help="pmcid")
    parser.add_argument('--source', action='store', default=EuroPMCLinks.DEFAULT_SOURCE,
                        help="article's source. MED = Default")
    parser.add_argument('--ebipmc_endpoint', action='store', type=str,
                        default=os.environ.get("EBIPMC_ENDPOINT", EuroPMCLinks.DEFAULT_ENDPOINT),
                        help=f"defauld: {EuroPMCLinks.DEFAULT_ENDPOINT}")

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-s', '--silent', action="store_true")

    args = parser.parse_args()

    if not args.verbose:
        if os.environ.get('VERBOSE'):
            args.verbose = True

    if args.silent:
        _log.disabled = True

    init_log(rootloglevel=logging.DEBUG if args.verbose else logging.INFO)

    api = EuroPMCLinks(args.ebipmc_endpoint)

    sys.stdout.write(json.dumps(api.query(args.source, args.pmcid)))
