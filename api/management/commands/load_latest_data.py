"""Load the data from the current OpenITI corpus on GitHub to the database.

This will update existing records in the database and create new ones if they don't exist yet.

IMPORTANT: before running the script, make sure you have pulled all changes from GitHub to your local machine.
"""

import json
import csv
from webbrowser import get
from django.db import models
from api.models import authorMeta, textMeta, versionMeta, personName, CorpusInsights, ReleaseMeta, ReleaseDetails, editionMeta, a2bRelation, relationType, placeMeta
from django.core.management.base import BaseCommand
import os
import re
import random
import itertools
import datetime

from openiti.git import get_issues   # TO DO: add issues!
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from openiti.helper.ara import deNoise, ar_cnt_file

from api.util.betaCode import betaCodeToArSimple
from api.util.utility import tags2dic, date_from_string, extract_metadata_from_header, collect_author_yml_data, collect_text_yml_data, collect_version_yml_data, set_analysis_priority


# define some global variables: 
VERBOSE = False
version_ids = dict()


class Command(BaseCommand):
    def handle(self, **options):
        relations_definitions_fp = "meta/relations_definitions.tsv"
        corpus_folder = r"D:/AKU/OpenITI/25Y_repos"
        tags_fp = "meta/ID_TAGS.txt"
        base_url = "https://raw.githubusercontent.com/OpenITI"
        release_code = "post-release"

        main(corpus_folder, relations_definitions_fp, tags_fp, base_url, release_code)


def main(corpus_folder, relations_definitions_fp, tags_fp, base_url, release_code):
    # load the relation types into the database:
    load_relations_definitions(relations_definitions_fp)

    # load Maxim's tags into a dictionary
    text_tags = tags2dic(tags_fp)
    print("tags loaded for", len(text_tags), "files")

    # load the corpus metadata:
    load_corpus_meta(corpus_folder, base_url, text_tags, release_code)

    # check for duplicate version_ids:
    for version_id, fn_list in version_ids.items():
        if len(fn_list) > 1:
            print("DUPLICATE ID:", version_id)
            print(fn_list)


def load_relations_definitions(relations_definitions_fp):
    """Load the definitions of the relation types into the database from a tsv file"""
    with open(relations_definitions_fp, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            if "descr" in row:
                descr = row["descr"]
            else:
                descr = ""
            reltype, created = relationType.objects.update_or_create(
                # selection keys:
                code=row["code"],
                subtype_code=row["subtype_code"],
                # update keys:
                defaults = dict(
                   name=row["name"],
                   name_inverted=row["name_inverted"],
                   descr=descr
                )
            )
            print(reltype, created)



def load_corpus_meta(corpus_folder, base_url, text_tags, release_code):
    """Load the metadata of the current corpus into the database
    
    Args:
        corpus_folder (str): path to the folder containing the 25-years folders
        base_url (str): the url to the folder on raw.github.com that contains the most current version of the text files
        text_tags (dict): a dictionary containing the tags Maxim gave to each version ID
            (key: version_id (str), value: list of tag strings)
        release_code (str): the release code (e.g., 2021.2.5; for the current GitHub repo, the release code is "post-release")
    """
    split_files = dict()  # TO DO: deal with split files!
    all_relation_types = dict()

    # create the release in the database (if it doesn't exist yet):
    release_obj, created = ReleaseDetails.objects.update_or_create(
        release_code=release_code,
        defaults=dict(
            release_date=datetime.date.today(),
            release_notes="Not yet released. Reflects the current status of the corpus on GitHub"
        )
    )

    for ah_folder in os.listdir(corpus_folder):
        # skip irrelevant folders: 
        if not re.findall("^\d{4}AH$", ah_folder):
            continue # skip anything that's not an xxxxAH folder
        if ah_folder == "9001AH":  # TO DO: load 9001AH folder!
            continue

        # create the path to the data folder that contains all the author folders:
        data_folder_pth = os.path.join(corpus_folder, ah_folder, "data")

        for author_uri in os.listdir(data_folder_pth):
            # create some author-level variables:
            texts = dict()
            author_folder_pth = os.path.join(data_folder_pth, author_uri)
            author_yml_fp = os.path.join(author_folder_pth, author_uri+".yml")
            

            # collect most of the author_meta from the author yml file
            # (Arabic names will be taken from the metadata headers 
            # if name information was not found in the yml files):
            if not os.path.exists(author_yml_fp):
                print("AUTHOR YML MISSING:", author_yml_fp)
                author_meta = dict()
            else:
                author_meta = collect_author_yml_data(author_yml_fp, author_uri)
            #print(json.dumps(author_meta, indent=2, ensure_ascii=False))

            # go through all text folders in the author folder and collect their metadata:
            for fn in os.listdir(author_folder_pth):
                fp = os.path.join(author_folder_pth, fn)
                if os.path.isdir(fp):
                    text_uri = fn
                    text_folder_pth = fp
                    text_yml_fp = os.path.join(text_folder_pth, text_uri+".yml")

                    # collect the text meta from the text yml file:
                    if not os.path.exists(text_yml_fp):
                        print("TEXT YML MISSING:", text_yml_fp)
                        text_meta = dict()
                    else:
                        text_meta = collect_text_yml_data(text_yml_fp, text_uri)
                    
                    # create an entry in the texts dictionary in which we store the text_meta
                    # and will store metadata for all versions of that text
                    # (we will use this to determine which version should be primary):
                    texts[text_uri] = {"text_meta": text_meta, "versions": []}
                    
                    for fn in os.listdir(text_folder_pth):
                        fp = os.path.join(text_folder_pth, fn)

                        # check how many periods the file contains
                        # (easy proxy for whether a text file has an extension, 
                        # whether a yml file is a book yml file or a version yml file):
                        split_fn = fn.split(".")
                        n_periods = len(split_fn)

                        # define what should be done with each file, based on its type:
                        if fn in ("README.md", "text_questionnaire.md"):
                            continue
                        elif n_periods < 3:
                            print("UNEXPECTED FILE with less than three periods:", fp)
                        elif fn.endswith("yml") and n_periods == 3:
                            text_yml_fp = fp  # the metadata from the text yml file has already been loaded above
                        elif fn.endswith("yml") and n_periods == 4:
                            version_yml_fp = fp
                            # collect the version metadata from the version yml file:
                            version_fp, version_meta = collect_version_yml_data(version_yml_fp, fn.strip(".yml"), 
                                                                                corpus_folder, base_url)
                            # collect additional metadata from the text file metadata headers:
                            r = collect_header_meta(version_fp, author_meta, text_meta, version_meta)
                            author_meta, text_meta, version_meta = r
                            # add Maxim's tags (organized by version_id) to the text's tags:
                            try:
                                text_meta["tags"] += text_tags[version_meta["version_id"]]
                            except:
                                #print("no text tags found for", version_meta["version_id"])
                                pass
                            # add the meta dictionaries to the texts dictionary:
                            texts[text_uri]["text_meta"] = text_meta  # update the text_meta that was already in the dictionary!
                            texts[text_uri]["versions"].append(version_meta)
                        elif re.findall(text_uri+r"\.[A-Z]\w+-[a-z]{3}\d(?:\.mARkdown|\.completed|\.inProgress)?", fn):
                            # load only the data from the most developed text file (.mARkdown > .completed > .inProgress > "")
                            # into the database; this is defined in the collect_version_yml_data function!
                            # version_fp = fp
                            # if n_periods == 2:
                            #     version_uri = fn
                            #     extension = ""
                            # elif n_periods == 3:
                            #     version_uri, extension = os.path.splitext(fn)

                            # add the version ID to the version_ids dictionary
                            # to check for duplicate IDs later:
                            version_id = split_fn[2].split("-")[0]
                            if not version_id in version_ids:
                                version_ids[version_id] = []
                            version_ids[version_id].append(fn)

                        else:
                            print(text_uri)
                            print("UNEXPECTED FILE:", fp)
                        
                elif fp.endswith(".yml"):
                    author_yml_fp = fp  # do nothing; author yml data has already been extracted
                else:
                    print(fp, "is not a folder nor an author yml file!")

            # ADD TO DATABASE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # add all metadata related to this author (incl. texts and versions) to the database:

            # 1. AUTHOR METADATA

            # add/update the author meta to the database:
            print(author_uri)

            am, am_created = authorMeta.objects.update_or_create(
                author_uri=author_uri,
                defaults = dict(
                    author_ar=author_meta['author_ar'],
                    author_lat=author_meta['author_lat'],
                    author_ar_prefered =author_meta['author_ar_prefered'],
                    author_lat_prefered =author_meta['author_lat_prefered'],
                    date=author_meta['date'],
                    date_AH=author_meta['date_AH'],
                    date_CE=author_meta['date_CE'],
                    date_str=author_meta['date_str'],
                    tags=author_meta['tags'],
                    bibliography=author_meta['bibliography'],
                    notes=author_meta['notes'],
                )
            )

            # add/update the author's name elements to the database (only once)
            for language, d in author_meta["name_elements"].items():
                personName.objects.update_or_create(
                    author_meta=am,
                    language=language,
                    defaults=dict(
                        shuhra=d["shuhra"],
                        kunya=d["kunya"],
                        ism=d["ism"],
                        laqab=d["laqab"],
                        nisba=d["nisba"]
                    )
                )
            
            # add/update the author's place relations to the database:
            for d in author_meta["place_relations"]:
                # first, add the place if it doesn't exist yet
                pb, created = placeMeta.objects.get_or_create(
                    thuraya_uri=d["place_b"]
                )

                # then, add the relation type if it doesn't exist yet:
                if not f'd["code"]_d["subtype_code"]' in all_relation_types:  # avoid extra lookup in database
                    rt, rt_created = relationType.objects.get_or_create(
                        code=d["code"], 
                        subtype_code=d["subtype_code"]
                    )
                    all_relation_types[f'd["code"]_d["subtype_code"]'] = rt
                else:
                    rt = all_relation_types[f'd["code"]_d["subtype_code"]']

                # then, add the relation: 
                rel, created = a2bRelation.objects.get_or_create(
                    person_a=am,
                    place_b=pb,
                    relation_type=rt
                )


            # add/update the author's person relations to the database:
            for d in author_meta["person_relations"]:
                # first, add the person if they don't exist yet
                if d["person_a"] == author_uri:
                    pa = am
                    pb, created = authorMeta.objects.get_or_create(
                        author_uri=d["person_b"]
                    )
                else:
                    pa, created = authorMeta.objects.get_or_create(
                        author_uri=d["person_a"]
                    )
                    pb = am

                # then, add the relation type if it doesn't exist yet:
                if not f'd["code"]_d["subtype_code"]' in all_relation_types:  # avoid extra lookup in database
                    rt, rt_created = relationType.objects.get_or_create(
                        code=d["code"], 
                        subtype_code=d["subtype_code"]
                    )
                    all_relation_types[f'd["code"]_d["subtype_code"]'] = rt
                else:
                    rt = all_relation_types[f'd["code"]_d["subtype_code"]']

                # then, add the relation: 
                rel, created = a2bRelation.objects.get_or_create(
                    person_a=pa,
                    person_b=pb,
                    relation_type=rt
                )

            # 2. TEXT METADATA

            for text_uri, text_d in texts.items():
                # prepare title fields before upload:
                text_meta = text_d["text_meta"]
                if "titles_ar_from_header" in text_meta and text_meta["titles_ar_from_header"]:
                    titles_ar = list(set(text_meta["titles_ar"] + text_meta["titles_ar_from_header"]))
                    text_meta['titles_ar'] = " :: ".join(titles_ar)
                if not text_meta["title_ar_prefered"] and text_meta["titles_ar"]:
                    text_meta["title_ar_prefered"] = text_meta["titles_ar"][0]
                
                # upload text meta to the database:
                tm, tm_created = textMeta.objects.update_or_create(
                    text_uri=text_meta["text_uri"],
                    author_meta=am,
                    defaults=dict(
                        titles_ar=text_meta['titles_ar'],
                        titles_lat=text_meta['titles_lat'],
                        title_ar_prefered = text_meta['title_ar_prefered'],
                        title_lat_prefered = text_meta['title_lat_prefered'],
                        text_type=text_meta["text_type"],
                        tags=" :: ".join(text_meta["tags"]),
                        bibliography=text_meta["bibliography"],
                        notes=text_meta["notes"],
                    )
                )

                # upload book relations to the database:

                for d in text_meta["text_relations"]:
                    # first, add the other text if it doesn't exist yet:
                    if d["text_a"] == text_uri:
                        ta = tm
                        pb, created = authorMeta.objects.get_or_create(
                            author_uri=d["text_b"].split(".")[0]
                        )
                        tb, created = textMeta.objects.get_or_create(
                            text_uri=d["text_b"],
                            author_meta=pb
                        )
                    else:
                        pa, created = authorMeta.objects.get_or_create(
                            author_uri=d["text_a"].split(".")[0]
                        )
                        ta, created = textMeta.objects.get_or_create(
                            text_uri=d["text_a"],
                            author_meta=pa
                        )
                        tb = tm

                    # then, add the relation type if it doesn't exist yet:
                    if not f'd["code"]_d["subtype_code"]' in all_relation_types:  # avoid extra lookup in database
                        rt, rt_created = relationType.objects.get_or_create(
                            code=d["code"], 
                            subtype_code=d["subtype_code"]
                        )
                        all_relation_types[f'd["code"]_d["subtype_code"]'] = rt
                    else:
                        rt = all_relation_types[f'd["code"]_d["subtype_code"]']

                    # then, add the relation: 
                    rel, created = a2bRelation.objects.get_or_create(
                        text_a=ta,
                        text_b=tb,
                        relation_type=rt
                    )

                # upload person relations to the database:

                for d in text_meta["person_relations"]:
                    # first, add the place if it doesn't exist yet
                    pb, created = authorMeta.objects.get_or_create(
                        author_uri=d["person_b"]
                    )

                    # then, add the relation type if it doesn't exist yet:
                    if not f'd["code"]_d["subtype_code"]' in all_relation_types:  # avoid extra lookup in database
                        rt, rt_created = relationType.objects.get_or_create(
                            code=d["code"], 
                            subtype_code=d["subtype_code"]
                        )
                        all_relation_types[f'd["code"]_d["subtype_code"]'] = rt
                    else:
                        rt = all_relation_types[f'd["code"]_d["subtype_code"]']

                    # then, add the relation: 
                    rel, created = a2bRelation.objects.get_or_create(
                        text_a=tm,
                        person_b=pb,
                        relation_type=rt
                    )

                # upload place/date relations to the database:

                for d in text_meta["place_relations"]:
                    # first, add the place if it doesn't exist yet
                    pb, created = placeMeta.objects.get_or_create(
                        thuraya_uri=d["place_b"]
                    )

                    # then, add the relation type if it doesn't exist yet:
                    if not f'd["code"]_d["subtype_code"]' in all_relation_types:  # avoid extra lookup in database
                        rt, rt_created = relationType.objects.get_or_create(
                            code=d["code"], 
                            subtype_code=d["subtype_code"]
                        )
                        all_relation_types[f'd["code"]_d["subtype_code"]'] = rt
                    else:
                        rt = all_relation_types[f'd["code"]_d["subtype_code"]']

                    # then, add the relation: 
                    rel, created = a2bRelation.objects.get_or_create(
                        text_a=tm,
                        place_b=pb,
                        relation_type=rt
                    )
                    

            # 3. VERSION METADATA
                # set the analysis priority ("pri", "sec") for all versions:
                text_d["versions"] = set_analysis_priority(text_d["versions"])

                for version_meta in text_d["versions"]:

                    # upload edition meta :
                    # NB: the edition meta comes mostly from the text files' metadata headers,
                    # except for the worldcat_url and pdf_url.
                    # The way we create these editionMeta objects,
                    # the same edition may be created multiple times if one or more
                    # fields are different; the alternative is that they overwrite each other,
                    # which is probably even less desirable:

                    em, em_created = editionMeta.objects.get_or_create(
                        text_meta=tm,
                        editor=version_meta["editor"],
                        edition_place=version_meta["edition_place"],
                        publisher=version_meta["publisher"],
                        edition_date=version_meta["edition_date"],
                        ed_info=version_meta["ed_info"],
                        worldcat_url=version_meta["worldcat_url"],
                        pdf_url=version_meta["pdf_url"]
                    )

                    # upload version metadata:

                    vm, vm_created = versionMeta.objects.update_or_create(
                        version_id=version_meta["version_id"],
                        version_uri=version_meta["version_uri"],
                        text_meta=tm,
                        language=version_meta["language"],
                        defaults=dict(
                            edition_meta=em,
                        )
                    )                    

                    # upload release version meta

                    rvm, rvm_created = ReleaseMeta.objects.update_or_create(
                        release=release_obj,
                        version_meta=vm,
                        defaults=dict(
                            url=version_meta["url"],
                            char_length=version_meta["char_length"],
                            tok_length=version_meta["tok_length"],
                            analysis_priority=version_meta["analysis_priority"],
                            annotation_status=version_meta["annotation_status"],
                            tags=version_meta["tags"],  # this is a string
                            notes=version_meta["notes"]
                        )
                    )


def collect_header_meta(version_fp, author_meta, text_meta, version_meta):
    """Collect the metadata from the metadata header of a text file and update
    the author_meta, text_meta and version_meta dictionaries accordingly"""
    header_meta = extract_metadata_from_header(version_fp)

    # - author name:

    if not author_meta["author_ar"]: # if no Arabic author name was taken from YML files:
        if "author_ar_from_header" not in author_meta:
            author_meta["author_ar_from_header"] = []
        author_meta["author_ar_from_header"] += list(set(header_meta["AuthorName"]))

    # - text title (combine with the uri's title component)

    if not text_meta["titles_ar"]: # if no title was taken from the YML file
        if "titles_ar_from_header" not in text_meta:
            text_meta["titles_ar_from_header"] = []
        text_meta["titles_ar_from_header"] += list(set(header_meta["Title"]))

    # - information about the current version's edition: 

    ed_info = header_meta["Edition:Editor"] +\
              header_meta["Edition:Place"] +\
              header_meta["Edition:Date"] +\
              header_meta["Edition:Publisher"]
    version_meta["editor"] = " :: ".join(header_meta["Edition:Editor"])
    version_meta["edition_place"] = " :: ".join(header_meta["Edition:Place"])
    version_meta["publisher"] = " :: ".join(header_meta["Edition:Publisher"])
    version_meta["edition_date"] = " :: ".join(header_meta["Edition:Date"])
    version_meta["ed_info"] = " :: ".join(ed_info)

    # - additional genre tags:
    version_id = version_meta["version_id"]
    try:
        coll_id = re.findall(r"^(\w+[a-zA-Z])\d{2,}(?:BK\d+|[A-Z])*", version_id)[0]
    except:
        print("no collection ID found in", version_id)
        input("continue?")

    tags = []
    for el in header_meta["Genre"]:
        for t in el.split(" :: "):
            if coll_id+"@"+t not in tags:
                tags.append(coll_id+"@"+t)
    
    return author_meta, text_meta, version_meta