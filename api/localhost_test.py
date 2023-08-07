"""Test whether all enpoints are working correctly.

To use this file, make sure the django application is running


Then simply run python -m localhost_test.py from another terminal.

"""

import requests


endpoints = [
    'all-releases/text-reuse-stats/ShamAY0034441_Shamela0009783BK1/',
    'all-releases/text-reuse-stats/all/',
    'all-releases/text-reuse-stats/',
    'all-releases/text-reuse-stats/ShamAY0034441/',

    '2022.2.7/text-reuse-stats/ShamAY0034441_Shamela0009783BK1/',
    '2022.2.7/text-reuse-stats/all/',
    '2022.2.7/text-reuse-stats/',
    '2022.2.7/text-reuse-stats/ShamAY0034441/',

    # release version endpoints:

    'all-releases/version/all/',
    'all-releases/version/',
    'all-releases/version/Shamela0009783BK1/',
    
    '2022.2.7/version/all/',
    '2022.2.7/version/',
    '2022.2.7/version/Shamela0009783BK1/',

    # text endpoints:  # TO DO: use other view for the texts  get_release_text

    'all-releases/text/',
    'all-releases/text/all/',
    'all-releases/text/0310Tabari.Tarikh/',

    '2022.2.7/text/',
    '2022.2.7/text/all/',
    '2022.2.7/text/0310Tabari.Tarikh/',

    # author endpoints:

    'all-releases/author/',
    'all-releases/author/all/',
    'all-releases/author/0310Tabari/',

    '2022.2.7/author/',
    '2022.2.7/author/all/',
    '2022.2.7/author/0310Tabari/',

    # release info endpoints:

    'all-releases/release-info/',
    '2022.2.7/release-info/',

    # A2BRelations endpoints (independent of releases):

    'relation/all/',
    'relation/',

    # relation types endpoint:
    'relation-type/all/',
    'relation-type/BORN/',

    # source collections info (independent of releases):

    'source-collection/all/',
    'source-collection/',
    'source-collection/Shamela/',

    # corpus insights (statistics on the number of books, largest book, etc. for each release):
    
    'all-releases/corpusinsights/',
    '2022.2.7/corpusinsights/',

    # Person names endpoints: 

    'person-name/all/',

    # GitHub Issues endpoints:

    'github-issue/all/',

    # should fail:
    '2022.2.7/nonexistent-endpoint/'
]

errors = []
VERBOSE = False
base_url = "http://127.0.0.1:7000/"
for url in endpoints:
    url = base_url + url
    response = requests.get(url)
    if VERBOSE:
        print(response.status_code, url)
    if response.status_code != 200:
        errors.append((response.status_code, url))
    #assert response.status_code == 200
print("All tests finished with", len(errors), "errors")
for error in errors:
    print(error)


