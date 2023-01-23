'''
https://europepmc.org/RestfulWebService#!/Europe32PMC32Articles32RESTful32API/dataLinks

'''

import requests
import logging
import xmltodict

from SNDGETL import init_log, ProcessingException

_log = logging.getLogger(__name__)


class EBIENAAPI:
    DEFAULT_ENDPOINT = "https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"

    def __init__(self, endpoint=DEFAULT_ENDPOINT):
        self.endpoint = endpoint

    def query(self, accessions):
        result = requests.get(self.endpoint.format(accession=",".join(accessions)))
        if result.ok:
            data = xmltodict.parse(result.text)["SAMPLE_SET"]
            for samples in data.values():
                for sample in samples:
                    yield sample
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

    parser = argparse.ArgumentParser(description='Gets samples from accessions')

    parser.add_argument('accessions', action='store', help="pmcid", nargs="+")

    parser.add_argument('--ebipmc_endpoint', action='store', type=str,
                        default=os.environ.get("EBIPMC_ENDPOINT", EBIENAAPI.DEFAULT_ENDPOINT),
                        help=f"default: {EBIENAAPI.DEFAULT_ENDPOINT}")

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-s', '--silent', action="store_true")

    args = parser.parse_args()

    if not args.verbose:
        if os.environ.get('VERBOSE'):
            args.verbose = True

    if args.silent:
        _log.disabled = True

    init_log(rootloglevel=logging.DEBUG if args.verbose else logging.INFO)

    api = EBIENAAPI(args.ebipmc_endpoint)
    for x in api.query(args.accessions):
        sys.stdout.write(json.dumps(x) + "\n")
