import math
import sys

'''
https://www.ebi.ac.uk/ebisearch/documentation/rest-api
https://www.ebi.ac.uk/ebisearch/metadata.ebi?db=sra-sample
'''
import requests
import logging

from SNDGETL import init_log, ProcessingException

_log = logging.getLogger(__name__)


class EBISearch:
    DEFAULT_ENDPOINT = "https://www.ebi.ac.uk/ebisearch/ws/rest/"
    DEFAULT_DB = "sra-sample"

    def __init__(self, domain=DEFAULT_DB, endpoint=DEFAULT_ENDPOINT, page_size=100):
        self.endpoint = endpoint
        self.domain = domain
        self.page_size = page_size
        self.queryParams = None
        self.total = None

    def query(self, query, start=0):
        self.queryParams = {"query": query, "size": self.page_size, "start": start}
        initial_curr_page = start
        logging.debug(f'initial_curr_page: {initial_curr_page}')
        data = self._query()
        for idx, doc in enumerate(data, 1):
            yield [doc, self.total, idx]
        for page in range(1, math.ceil(self.total / self.page_size)):
            data = self._query()
            for idx, doc in enumerate(data, self.page_size + 1):
                yield [doc, self.total, idx]

    def _query(self):
        headers = {'Accept': 'application/json'}
        result = requests.get(self.endpoint + self.domain, self.queryParams,headers=headers)

        if result.ok:
            try:
                data = result.json()
            except:
                logging.debug(result.text)
                raise
            self.queryParams["start"] = self.queryParams["start"] + self.queryParams["size"]
            logging.debug(f'offset: {self.queryParams["start"]}')
            self.total = int(data["hitCount"])
            try:
                x = data["entries"]
                return x
            except:
                print(result)
                return None
        else:
            ex = ProcessingException("error in http request",
                                     data=[self.endpoint, self.queryParams, result.status_code, result.text])
            logging.error("error executing page handler", exc_info=ex)
            raise ex


if __name__ == "__main__":
    import os
    import json
    import argparse
    from tqdm import tqdm
    import datetime

    parser = argparse.ArgumentParser(description='Retreives EBI data entries')

    parser.add_argument('--ebipmc_endpoint', action='store', type=str,
                        default=os.environ.get("EBIPMC_ENDPOINT", EBISearch.DEFAULT_ENDPOINT),
                        help=f"defauld: {EBISearch.DEFAULT_ENDPOINT}")

    parser.add_argument('--page_size', action='store', type=int,
                        default=500)

    parser.add_argument('--offset', action='store', type=int, default=None)

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-s', '--silent', action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    query_subparser = subparsers.add_parser('query')
    query_subparser.add_argument('domain', action='store',
                                 help="EBI domain / database", nargs="?")
    query_subparser.add_argument('ebi_query', action='store',
                                 help="query to the EBI PMC Site", nargs="?")

    aff_subparser = subparsers.add_parser('country')
    aff_subparser.add_argument('country', action="store", help="sample country")
    aff_subparser.add_argument('--fromdate', action='store', help="ISO FORMAT: %Y-%m-%d",
                               type=datetime.date.fromisoformat, default=None)



    args = parser.parse_args()

    if not args.verbose:
        if os.environ.get('VERBOSE'):
            args.verbose = True

    if args.silent:
        _log.disabled = True

    init_log(rootloglevel=logging.DEBUG if args.verbose else logging.INFO)

    params = {"format": "json"}
    if args.offset:
        params["offSet"] = args.offset


    if args.command == "query":
        query = args.ebi_query
        domain = args.domain
    elif args.command == "country":
        domain = "sra-sample"
        query = f"country:{args.country.strip()}"
        if args.fromdate:
            fromdate = args.fromdate.strftime('%Y-%m-%d')
            todate = datetime.datetime.now()
            todate = datetime.date(todate.year + 3, 12, 31)
            todate = todate.strftime('%Y-%m-%d')
            #(first_public_date:["2020-01-01" TO "2024-12-31"])
            query = query + f" AND first_public_date:[{fromdate} TO {todate}]"


    _log.debug(domain + "?" + query)

    api = EBISearch(domain, args.ebipmc_endpoint,page_size=args.page_size)

    with tqdm(api.query(query)) as pbar:
        for qresult, totalPages, qcurr_page in pbar:

            if not pbar.total:
                pbar.total = totalPages
                pbar.initial = qcurr_page
                pbar.update(qcurr_page)
                pbar.refresh()

            print(json.dumps(qresult))
