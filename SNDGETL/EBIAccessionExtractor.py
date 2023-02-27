import logging

from SNDGETL import init_log

_log = logging.getLogger(__name__)


class EBIAccessionExtractor(object):
    """
    Genes & Proteins                                         2111
    Nucleotide Sequences                                     1094
    GOA Project                                               239
    BioStudies: supplemental material and supporting data     219
    Chemicals                                                 194
    GEO                                                       185
    Chembl                                                    156
    Protein Structures                                        143
    SNPs                                                      122
    Diseases                                                  118
    BioProject                                                 58
    RefSeq                                                     46
    FlyBase                                                    27
    Clinical Trials                                            25
    Functional Genomics Experiments                            21
    Pfam                                                       13
    ProteomeXchange                                            13
    HPA                                                        12
    Protein Families                                           11
    RRID                                                       10
    Ensembl                                                     9
    COSMIC                                                      9
    Data Citations                                              8
    Quick GO                                                    5
    DisProt                                                     4
    IGSR | samples - 1000 Genomes                               2
    Dryad Data Platform                                         2
    Cellosaurus                                                 2
    Rfam                                                        2
    dbGaP                                                       1
    Reactome                                                    1
    Electron Microscopy Data Bank                               1
    GCA                                                         1
    European Genome-Phenome Archive                             1
    Faculty Opinions                                            1
    Mouse Genome Informatics (MGI)                              1
    EBiSC                                                       1
    Proteomics Data                                             1
    """

    PUBLICATION_DEFAULT_DS = "literature"

    DEFAULT_TYPE_FILE_MAP = {
        "Nucleotide Sequences": "seqs.csv",
        "RefSeq": "assemblies.csv",
        "Genes & Proteins": "genes.csv",
        "BioProject": "projects.csv",
        "Chembl": "chembl.csv",
        "SNPs": "snps.csv",
        "Protein Structures": "pdb.csv",
        "GEO": "geos.csv",
        PUBLICATION_DEFAULT_DS: "publications.csv"
    }

    def __init__(self, workdir, type_file_map=DEFAULT_TYPE_FILE_MAP):
        self.workdir = workdir
        self.type_file_map = type_file_map
        self.handler_map = {}

    def __enter__(self):
        for k, v in self.type_file_map.items():
            self.handler_map[k] = open(self.workdir + "/" + v, "w")

    def __exit__(self, exc_type, exc_value, traceback):
        for v in self.handler_map.values():
            v.close()

    def links_entry(self, data):
        assert self.handler_map, "object not initialized"
        if data["Name"] in self.type_file_map:
            for sec in data["Section"]:
                for link in sec["Linklist"]["Link"]:
                    yield (EBIAccessionExtractor.PUBLICATION_DEFAULT_DS, link["Source"]["Identifier"]["IDScheme"],
                           link["Source"]["Identifier"]["ID"], "")
                    yield (data["Name"], link["Target"]["Identifier"]["IDScheme"], link["Target"]["Identifier"]["ID"],
                           link["Target"]["Title"])
                    """
                    if data["Name"] == "Nucleotide Sequences":
                        yield data["Name"], link["Target"]["Identifier"]["ID"], link["Target"]["Identifier"]["Title"]
                    if data["Name"] == "RefSeq":
                        yield data["Name"], link["Target"]["Identifier"]["ID"], link["Target"]["Identifier"]["Title"]
                    """

    def save_data(self, data):
        for ds, scheme, rid, title in self.links_entry(data):
            if (ds == "Nucleotide Sequences") and (".." in rid):
                continue
            self.handler_map[ds].write(f'{scheme},{rid},"{title}"\n')


if __name__ == "__main__":
    import os
    import argparse
    import json

    parser = argparse.ArgumentParser(description='extracts ids from EuroPMCLinks script')

    parser.add_argument('json_load', action='store', help="json created by EuroPMCLinks script")
    parser.add_argument('workdir', action='store', help="dir to save the accession numbers")

    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-s', '--silent', action="store_true")

    args = parser.parse_args()

    if not args.verbose:
        if os.environ.get('VERBOSE'):
            args.verbose = True

    if args.silent:
        _log.disabled = True

    init_log(rootloglevel=logging.DEBUG if args.verbose else logging.INFO)

    if not os.path.exists(args.workdir):
        os.makedirs(args.workdir)
    assert os.path.exists(args.workdir), f"'{args.workdir}' could not be created"

    eae = EBIAccessionExtractor(args.workdir)
    with eae, open(args.json_load) as h:
        for l in h:
            try:
                data = json.loads(l)
                eae.save_data(data)
            except KeyError as ex:
                _log.error(json.dumps(data, indent=2))
                _log.error(ex)
                raise
