#!/usr/bin/env nextflow

/*
 * loads raw data from ebi/ncbi databases given a query
 * (FIRST_PDATE:[2018-07-04 TO 2026-12-31])
 */
params.query = "AFF:Argentina AND HAS_XREFS:y AND sort_date:y"
params.solr_endpoint = "$baseDir/data/sample.fa"

process query_eupmc {

    input:
    val query

    output:
    stdout


    """

    python -m "SNDGETL.EuroPMC"  "vishnopolska AND HAS_XREFS:y AND sort_date:y" --page_size 3
    """
}


workflow {
    query_eupmc(params.query) | view
}