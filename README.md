# SNDG ETL

## Download data associated with a publication

echo '#python -m "SNDGETL.EuroPMC" affiliation Argentina --fromdate %Y-%m-%d' > "publications_$(date +"%Y_%m_%d").json"
python -m "SNDGETL.EuroPMC" Argentina --fromdate %Y-%m-%d >> "publications_$(date +"%Y_%m_%d").json"

python -m "SNDGETL.EuroPMCLinks" load_json  publications_(fecha_x).json > "pub_links_$(date +"%Y_%m_%d").json"

## Download data associated with the localization of the sample

python -m "SNDGETL.EBISearch" country Argentina --fromdate %Y-%m-%d > "samples_$(date +"%Y_%m_%d").json"

## Transform links to accessions
python -m "SNDGETL.EBIAccessionExtractor" pub_links_(fecha_x).json ./workdir