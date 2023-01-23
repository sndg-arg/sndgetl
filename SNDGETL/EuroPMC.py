import math
import sys

'''
http://europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf
https://europepmc.org/RestfulWebService#!/Europe32PMC32Articles32RESTful32API/dataLinks
https://dev.elsevier.com/sc_search_views.html
(FIRST_PDATE:[2018-07-04 TO 2026-12-31])
sort_date:y
'''
import requests
import logging

from SNDGETL import init_log, ProcessingException

_log = logging.getLogger(__name__)


class EuroPMC:
    DEFAULT_ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def __init__(self, endpoint=DEFAULT_ENDPOINT):
        self.endpoint = endpoint
        self.queryParams = None
        self.total = None
        self.nextPageUrl = None

    def query(self, query, pageSize=100, resultType="core", **queryParams):
        self.queryParams = {k: v for k, v in queryParams.items()}
        self.queryParams.update({"query": query, "pageSize": pageSize, "resulttype": resultType})
        initial_curr_page = queryParams.get("offSet", 0)
        logging.debug(f'initial_curr_page: {initial_curr_page}')
        for idx, doc in enumerate(self._query(), 1):
            yield [doc, self.total, initial_curr_page * pageSize + idx]
        # print("--------------------")

        if self.nextPageUrl:
            rango = list(range(initial_curr_page + 1, math.ceil(self.total / pageSize)))
            for curr_page in rango:
                assert self.nextPageUrl
                for idx, doc in enumerate(self._query()):
                    yield [doc, self.total, curr_page * pageSize + idx]

    def _query(self):
        if self.nextPageUrl:
            result = requests.get(self.nextPageUrl)
        else:
            result = requests.get(self.endpoint, self.queryParams)

        if result.ok:
            data = result.json()
            self.nextPageUrl = data.get("nextPageUrl", None)
            logging.debug(f'nextPageUrl: {self.nextPageUrl}')
            self.total = int(data["hitCount"])
            try:
                x = data["resultList"]["result"]
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

    parser = argparse.ArgumentParser(description='Detects active site from PDB of a given ligand')

    parser.add_argument('--ebipmc_endpoint', action='store', type=str,
                        default=os.environ.get("EBIPMC_ENDPOINT", EuroPMC.DEFAULT_ENDPOINT),
                        help=f"defauld: {EuroPMC.DEFAULT_ENDPOINT}")
    parser.add_argument('--page_size', action='store', type=int,
                        default=25)
    parser.add_argument('--result_type', action='store', choices=["idlist", "lite", "core"],
                        default="core")
    parser.add_argument('--offset', action='store', type=int, default=None)
    parser.add_argument('--sort', action='store', type=str, default="P_PDATE_D ASC")

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-s', '--silent', action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    query_subparser = subparsers.add_parser('query')
    query_subparser.add_argument('ebi_query', action='store',
                                 help="query to the EBI PMC Site", nargs="?")

    aff_subparser = subparsers.add_parser('affiliation')

    aff_subparser.add_argument('affiliation', action="store",
                               help="word to search in the affiliation")

    aff_subparser.add_argument('--fromdate', action='store', help="ISO FORMAT: %Y-%m-%d",
                               type=datetime.date.fromisoformat, default=None)

    aff_subparser.add_argument('--no_refs', action="store_true",
                               help="bring articles with no data")

    args = parser.parse_args()

    if not args.verbose:
        if os.environ.get('VERBOSE'):
            args.verbose = True

    if args.silent:
        _log.disabled = True

    init_log(rootloglevel=logging.DEBUG if args.verbose else logging.INFO)

    api = EuroPMC(args.ebipmc_endpoint)

    params = {"format": "json"}
    if args.offset:
        params["offSet"] = args.offset
    if args.sort:
        params["sort"] = args.sort

    if args.command == "query":
        query = args.ebi_query
    elif args.command == "affiliation":
        with_refs = "n" if args.no_refs else "y"
        query = f"AFF:{args.affiliation} AND HAS_XREFS:{with_refs} AND sort_date:y"

        if args.fromdate:
            fromdate = args.fromdate.strftime('%Y-%m-%d')
            todate = datetime.datetime.now()
            # No funca la API si pones algunas fechas es raro. Por eso la fecha de fin de año
            todate = datetime.date(todate.year + 3, 12, 31)
            todate = todate.strftime('%Y-%m-%d')
            query = query + f" AND FIRST_PDATE:[{fromdate} TO {todate}]"
    _log.debug(query)
    with tqdm(api.query(query, pageSize=args.page_size, **params)) as pbar:
        for qresult, totalPages, qcurr_page in pbar:

            if not pbar.total:
                pbar.total = totalPages
                pbar.initial = qcurr_page
                pbar.update(qcurr_page)
                pbar.refresh()

            print(json.dumps(qresult))
