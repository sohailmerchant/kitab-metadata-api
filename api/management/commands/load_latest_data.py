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

from openiti.helper.uri import URI, check_yml_files
from openiti.git import get_issues
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from openiti.helper.ara import deNoise, ar_cnt_file

from api.betaCode import betaCodeToArSimple



VERBOSE = False
geo_URIs = dict()
version_ids = dict()
text_rel_d = dict()
all_header_meta = dict()


lunar_months = """\
01	MUH
02	SAF
03	RA1
04	RA2
05	JU1
06	JU2
07	RAJ
08	SHC
09	RAM
10	SHW
11	DHQ
12	DHH""".split("\n")
lunar_months = {row.split("\t")[1]: row.split("\t")[0] for row in lunar_months}

# define a metadata category for all relevant items in the text file headers:
headings_dict = {  
     'Iso' : "Title", 
     'Lng' : "AuthorName",
     'higrid': "Date",
     'HigriD': "Date",
     'auth' : "AuthorName",
     'auth.x' : "AuthorName",
     'bk' : "Title", # 
     'cat' : "Genre", # Values: max 3-digit integer
     'name' : "Genre", 
     'البلد' : "Edition:Place", 
     'الطبعة' : "Edition:Date", # date + number (al-ula, al-thaniya, ...)
     'الكتاب' : "Title", 
     'المؤلف' : "AuthorName", 
     'المحقق' : "Edition:Editor", 
     'الناشر' : "Edition:Publisher", 
     'تأليف' : "AuthorName", 
     'تحقيق' : "Edition:Editor", 
     'تقديم وتعليق' : "Edition:Editor", 
     'حققه' : "Edition:Editor", 
     'خرج أحاديثه' : "Edition:Editor", 
     'دار النشر' : "Edition:Publisher", 
     'دراسة وتحقيق' : "Edition:Editor", 
     'سنة الطبع' : "Edition:Date", 
     'سنة النشر' : "Edition:Date", 
     'شهرته' : "AuthorName", 
     'عام النشر' : "Edition:Date", 
     'مكان النشر' : "Edition:Place", 
     'وضع حواشيه' : "Edition:Editor", 
     'أشرف عليه وراجعه وقدم له' : "Edition:Editor", # thesis supervisor
     'أصدرها':  "Edition:Editor",
     'أعتنى به' : "Edition:Editor",
     'أعد أصله' : "Edition:Editor",
     'أعده' : "Edition:Editor",
     'أعده للنشر' : "Edition:Editor",
     'أعده ونشره' : "Edition:Editor",
     'ألحقها' : "Edition:Editor",
     'تقديم وإشراف ومراجعة' : "Edition:Editor", 
     '010.AuthorAKA' : "AuthorName", 
     '010.AuthorNAME' : "AuthorName",
     '001.AuthorNAME' : "AuthorName",
     '011.AuthorDIED' : "Date", 
     '019.AuthorDIED' : "Date",
     '006.AuthorDIED' : "Date", 
     '020.BookTITLE' : "Title",
     '010.BookTITLE' : "Title",
     '021.BookSUBJ' : "Genre", # separated by :: 
     '029.BookTITLEalt' : "Title", 
     '040.EdEDITOR' : "Edition:Editor", 
     '043.EdPUBLISHER' : "Edition:Publisher",
     '013.EdPUBLISHER' : "Edition:Publisher",
     '044.EdPLACE' : "Edition:Place", 
     '045.EdYEAR' : "Edition:Date",
     '015.BookGENRE' : "Genre",
     'title' : "Title",
     'title_ar': "Title",
     'نام كتاب': "Title",
     'نويسنده': "AuthorName",
     'ناشر' : "Edition:Publisher",
     'تاريخ نشر' : "Edition:Date",
     'مكان چاپ' : "Edition:Place",
     'محقق/ مصحح' : "Edition:Editor",
     'مصحح' : "Edition:Editor",
     'محقق' : "Edition:Editor",
     'تاريخ نشر' : "Edition:Date",
     'تاريخ وفات مؤلف' : "Date",
     'موضوع' : "Genre",
     'Title' : "Title",
     'title' : "Title",
     'Editor': "Edition:Editor",
     'Publisher': "Edition:Publisher",
     'Place of Publication': "Edition:Place",
     'Date of Publication': "Edition:Date",
     'Author': "AuthorName",
     'author': "AuthorName",
     'source': "Edition:Place",  # in PAL texts: manuscript data
     'Date': "Date",
     }


class Command(BaseCommand):
    def handle(self, **options):
        relations_definitions_fp = "relations_definitions.tsv"
        corpus_folder = r"D:/AKU/OpenITI/25Y_repos"
        tags_fp = "ID_TAGS.txt"
        base_url = "https://raw.githubusercontent.com/OpenITI"
        release_code = "post-release"


        main(corpus_folder, relations_definitions_fp, tags_fp, base_url, release_code)


def main(corpus_folder, relations_definitions_fp, tags_fp, base_url, release_code):
    # set the path separator to forward slash:
    os.sep = "/"
    # load the relation types into the database:
    load_relations_definitions(relations_definitions_fp)
    # load Maxim's tags into a dictionary
    text_tags = load_tags(tags_fp)
    print("tags loaded for", len(text_tags), "files")
    # load the corpus metadata:
    load_corpus_meta(corpus_folder, base_url, text_tags, release_code)


def ah2ce(date):
    """convert AH date to CE date"""
    return 622 + (int(date) * 354 / 365.25)

def load_relations_definitions(fp):
    with open(fp, mode="r", encoding="utf-8") as file:
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

def load_tags(tags_fp):
    """Load tags from the tags/genre file created by Maxim."""
    with open(tags_fp, "r", encoding="utf8") as f1:
        dic = {}
        data = f1.read().split("\n")

        for d in data:
            version_id, tags = d.split("\t")
            dic[version_id] = tags.split(";")
    return dic

def load_corpus_meta(corpus_folder, base_url, text_tags, release_code):
    statusDic = {}
    split_files = dict()
    for ah_folder in os.listdir(corpus_folder):
        if not re.findall("^\d{4}AH$", ah_folder):
            continue # skip anythin that's not an xxxxAH folder
        if ah_folder == "9001AH":  # TO DO: load 9001AH folder!
            continue
        data_folder_pth = os.path.join(corpus_folder, ah_folder, "data")
        for author_uri in os.listdir(data_folder_pth):
            texts = dict()
            author_folder_pth = os.path.join(data_folder_pth, author_uri)
            author_yml_fp = os.path.join(author_folder_pth, author_uri+".yml")
            # collect most of the author_meta from the author yml file
            # (Arabic names will be taken from the metadata headers 
            # if name information was not found in the yml files)
            author_meta = collect_author_yml_data(author_yml_fp, author_uri)
            #print(json.dumps(author_meta, indent=2, ensure_ascii=False))

            if not os.path.exists(author_yml_fp):
                print("AUTHOR YML MISSING:", author_yml_fp)

            for fn in os.listdir(author_folder_pth):
                fp = os.path.join(author_folder_pth, fn)
                if os.path.isdir(fp):
                    text_uri = fn
                    text_folder_pth = fp
                    text_yml_fp = os.path.join(text_folder_pth, text_uri+".yml")
                    if not os.path.exists(text_yml_fp):
                        print("BOOK YML MISSING:", text_yml_fp)
                    else:
                        # collect the text meta from the text yml file:
                        text_meta = collect_text_yml_data(text_yml_fp, text_uri)
                        texts[text_uri] = {"text_meta": text_meta, "versions": []}
                    for fn in os.listdir(text_folder_pth):
                        fp = os.path.join(text_folder_pth, fn)
                        split_fn = fn.split(".")
                        n_periods = len(split_fn)
                        if fn in ("README.md", "text_questionnaire.md"):
                            pass
                        elif n_periods < 3:
                            print("UNEXPECTED FILE with less than three periods:", fp)
                        elif fn.endswith("yml") and n_periods == 3:
                            text_yml_fp = fp
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
                            # add the meta dictionaries to the aggregator:
                            texts[text_uri]["text_meta"] = text_meta
                            texts[text_uri]["versions"].append(version_meta)
                        elif re.findall(text_uri+r"\.[A-Z]\w+-[a-z]{3}\d(?:\.mARkdown|\.completed|\.inProgress)?", fn):
                            version_fp = fp
                            if n_periods == 2:
                                version_uri = fn
                                extension = ""
                            elif n_periods == 3:
                                version_uri, extension = os.path.splitext(fn)
                            version_id = split_fn[2].split("-")[0]

                            # add the version ID to the version_ids dictionary
                            # to check for duplicate IDs later:
                            if not version_id in version_ids:
                                version_ids[version_id] = []
                            version_ids[version_id].append(fn)

                        else:
                            print(text_uri)
                            print("UNEXPECTED FILE:", fp)
                        
                elif fp.endswith(".yml"):
                    text_yml_fp = fp
                else:
                    print(fp, "is not a folder nor a text yml file!")

            # ADD TO DATABASE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # add all metadata related to this author (incl. texts and versions) to the database:

            # 0. RELEASE METADATA

            # create the release (if it doesn't exist yet):
            release_id, created = ReleaseDetails.objects.update_or_create(
                release_code = release_code
            )

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
                rt, rt_created = relationType.objects.get_or_create(
                    code=d["code"], 
                    subtype_code=d["subtype_code"]
                )

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
                rt, rt_created = relationType.objects.get_or_create(
                    code=d["code"], 
                    subtype_code=d["subtype_code"]
                )

                # then, add the relation: 
                rel, created = a2bRelation.objects.get_or_create(
                    person_a=pa,
                    person_b=pb,
                    relation_type=rt
                )

            # 2. TEXT METADATA

            for text_d in texts:
                text_meta = text_d["text_meta"]
                titles_ar = list(set(text_meta["titles_ar"] + text_meta["titles_ar_from_header"]))
                titles_ar = " :: ".join(titles_ar)

                # TO DO / TO BE CONTINUED: check if we need to change title_ar_prefered?


                tm, tm_created = textMeta.objects.update_or_create(
                    text_uri=text_meta["text_uri"],
                    author_meta=am,
                    defaults=dict(
                        titles_ar=titles_ar,
                        titles_lat=text_meta['titles_lat'],
                        title_ar_prefered = text_meta['title_ar_prefered'],
                        title_lat_prefered = text_meta['title_lat_prefered'],
                        text_type=text_meta["text_type"],
                        tags=" :: ".join(text_meta["tags"])
                    )
                )

    # text_meta = dict(
    #     text_uri=text_uri,
    #     author_meta="",
    #     titles_ar=" :: ".join(title_ar),
    #     titles_lat=" :: ".join(title_lat),
    #     title_ar_prefered=title_ar_prefered,
    #     title_lat_prefered=title_lat_prefered,
    #     text_type="text",
    #     tags=tags,
    #     bibliography=bibliography,
    #     notes=notes,
    #     place_relations=place_relations,
    #     text_relations=text_relations
    # )


            # 3. VERSION METADATA
                for version_d in text_d["versions"]:
                    pass

            





def date_from_string(s):
    """Convert a date string YEAR-MON-DA (X+ for unknown) to a date"""
    if not s.strip():
        return ["", ""]
    
    year, month, day = s.split("-")
    day = day[:2].strip()
    start_year = re.sub("[Xx]", "0", year)
    end_year = re.sub("[Xx]", "9", year)
    if re.findall("[Xx]", month):
        start_month = "01"
        end_month = "12"
    else:
        try:
            start_month = lunar_months[month]
            end_month = lunar_months[month]
        except:
            start_month = month
            end_month = month
    start_day = re.sub("[Xx]", "0", day)
    end_day = re.sub("[Xx]", "9", day)
    if int(start_day) < 1:
        start_day = "01"
    if int(end_day) > 30:
        start_day = "30"
    return [f"{start_year}-{start_month}-{start_day}", f"{end_year}-{end_month}-{end_day}"]
    

def collect_header_meta(version_fp, author_meta, text_meta, version_meta):
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



def collect_version_yml_data(version_yml_fp, version_uri, corpus_folder, base_url):
    version_id = version_uri.split("-")[0].split(".")[-1]
    language = version_uri.split("-")[1][:3]

    vers_d = readYML(version_yml_fp)

    # - explicit primary version:

    primary_yml = ""
    if "PRIMARY_VERSION" in vers_d["90#VERS#ISSUES###:"]:
        primary_yml = "pri"

    # - most developed text version:

    pth = version_yml_fp.strip(".yml")
    extensions = [".mARkdown", ".completed", ".inProgress", ""]
    for ext in [".mARkdown", ".completed", ".inProgress", ""]:
        version_fp = pth + ext
        if os.path.exists(version_fp):
            break
        elif ext == "":
            print("NO TEXT VERSION FOUND FOR THIS YML FILE:", version_yml_fp)

    # - url:

    url = version_fp.replace(corpus_folder, base_url)

    # annotation status:

    if not ext:
        annotation_status = "(not yet annotated)"
    else:
        annotation_status = ext[1:]

    # - length in number of characters and (Arabic-script) tokens:

    tok_length = vers_d["00#VERS#LENGTH###:"].strip()
    char_length = vers_d["00#VERS#CLENGTH##:"].strip()
    # recalculate the length if it is not present in the yml file:
    if not (tok_length and char_length):
        if not char_length:
            char_length = ar_cnt_file(version_fp, mode="char")
            char_length = str(char_length)
            vers_d["00#VERS#CLENGTH##:"] = char_length
        if not tok_length:
            tok_length = ar_cnt_file(version_fp, mode="token")
            tok_length = str(tok_length)
            vers_d["00#VERS#LENGTH###:"] = tok_length
        # store the recalculated lengths in the yml file:
        ymlS = dicToYML(vers_d)
        with open(versF, mode="w", encoding="utf-8") as file:
            file.write(ymlS)

    # - edition_link:

    world_cat_link = ""
    if "80#VERS#BASED####:" in vers_d:
        if vers_d["80#VERS#BASED####:"] and not vers_d["80#VERS#BASED####:"].strip().startswith("permalink"):
            world_cat_link = vers_d["80#VERS#BASED####:"].strip()
            world_cat_link = re.sub(r"[\s¶]*,[\s¶]", ",", world_cat_link)
    else:
        print("MISSING KEY: 80#VERS#BASED####: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        input()
    
    pdf_link = ""
    if "80#VERS#LINKS####:" in vers_d:
        if vers_d["80#VERS#LINKS####:"] and not vers_d["80#VERS#LINKS####:"].strip().startswith("all@id"):
            pdf_link = vers_d["80#VERS#LINKS####:"].strip()
            pdf_link = re.sub(r"[\s¶]*,[\s¶]", ",", pdf_link)
    else:
        print("MISSING KEY: 80#VERS#LINKS####: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        input()

    # - notes:
    notes = ""
    if "90#VERS#COMMENT##:" in vers_d:
        if vers_d["90#VERS#COMMENT##:"] and not vers_d["90#VERS#COMMENT##:"].strip().startswith("a free running comment"):
            notes = vers_d["90#VERS#COMMENT##:"].strip()
            notes = re.sub(r"    ", "", notes)
    else:
        print("MISSING KEY: 90#BOOK#COMMENT##: in", text_uri)
        print(json.dumps(text_d, indent=2, ensure_ascii=False))
        input()

    # - issues: 
    version_tags = re.findall("[A-Z_]{5,}", vers_d["90#VERS#ISSUES###:"])

    version_meta = dict(
        # version_meta:
        version_id=version_id,
        version_uri=version_uri,
        text_meta="",
        language=language,
        tags=" :: ".join(version_tags),
        edition_meta="",
        # release_version_meta:
        char_length=char_length,
        tok_length=tok_length,
        url=url,
        analysis_priority=primary_yml,
        annotation_status=annotation_status,
        notes=notes,
        # edition_meta:
        world_cat_link=world_cat_link,
        pdf_link=pdf_link
    )

    return version_fp, version_meta


def collect_text_yml_data(text_yml_fp, text_uri):
    text_d = readYML(text_yml_fp)

    # - title:
    title_lat = []
    title_ar = []
    if text_d:
        for c in ["10#BOOK#TITLEA#AR:", "10#BOOK#TITLEB#AR:"]:
            if not ("al-Muʾallif" in text_d[c]\
                    or "none" in text_d[c].lower()):
                title_lat.append(text_d[c].strip())
                title_ar.append(betaCodeToArSimple(title_lat[-1]))
    title_from_uri = re.sub("([A-Z])", r" \1", text_uri.split(".")[1]).strip()
    title_from_uri = title_from_uri.replace("c", "ʿ").replace("C", "ʿ")
    title_lat.append(title_from_uri)
    title_lat_prefered = title_lat[0]
    if title_ar:
        title_ar_prefered = title_ar[0]
    else: 
        title_ar_prefered = ""

    # - tags
    tags = []
    if text_d["10#BOOK#GENRES###:"] and not text_d["10#BOOK#GENRES###:"].startswith("src"):
        for genre in re.split("[\s¶]*[,:;]+[\s¶]*", text_d["10#BOOK#GENRES###:"]):
            tags.append(genre)

    # - text date:
    place_relations = []
    places = []
    if text_d["20#BOOK#WROTE####:"] and not text_d["20#BOOK#WROTE####:"].startswith("URIs from Althurayya"):
        for place in re.split("[\s¶]*[:,;]+[\s¶]*", text_d["20#BOOK#WROTE####:"]):
            places.append(place)
    dates = []
    if text_d["30#BOOK#WROTE##AH:"] and not text_d["30#BOOK#WROTE##AH:"].startswith("YEAR-MON-DA"):
        for date in re.split("[\s¶]*[:,;]+[\s¶]*", text_d["30#BOOK#WROTE##AH:"]):
            dates.append(date)
    if places:
        if len(dates) <= len(places):
            for i, place in enumerate(places):
                try:
                    date = dates[i]
                except:
                    date = ""
                start, end = date_from_string(date)
                place_relations.append(dict(text_a=text_uri, code="WRITTEN", subtype_code="", 
                                            place_b=place, start_date_AH=start, end_date_AH=end))
        else:
            for i, date in enumerate(dates):
                start, end = date_from_string(date)
                try:
                    place = places[i]
                except:
                    place = "UNDEFINED"
                place_relations.append(dict(text_a=text_uri, code="WRITTEN", subtype_code="", 
                                            place_b=place, start_date_AH=start, end_date_AH=end))


    # - text relations:
    text_relations = []
    if not "40#BOOK#RELATED##:" in text_d:
        print("MISSING KEY 40#BOOK#RELATED##: in", text_uri)
    else:
        if text_d["40#BOOK#RELATED##:"].strip() and not text_d["40#BOOK#RELATED##:"].strip().startswith("URI of"):
            rels = text_d["40#BOOK#RELATED##:"].strip()
            rels = re.sub(" *[\r\n¶]+ *", " ", rels)
            rels = re.split(" *[;:]+ *", rels)
            for rel in rels:
                rel = re.sub(" +", " ", rel)
                if "@" in rel:
                    rel_types = rel.split("@")[0]
                    rel_text = rel.split("@")[1]
                else:
                    try:
                        rel_types = re.findall("\(([^\)]+)", rel)[0]
                    except:
                        print(text_uri, ":")
                        print("    no relationship type found in ", rel)
                        continue
                    rel_text = re.sub(" *\(.+", "", rel).strip()
                
                
                if not text_uri in text_rel_d:
                    text_rel_d[text_uri] = []
                if not rel_text in text_rel_d:
                    text_rel_d[rel_text] = []
                for rel_type in re.split(" *, *", rel_types):
                    if "." in rel_type:
                        main_rel_type = re.split(" *\. *", rel_type)[0]
                        sec_rel_type = re.split(" *\. *", rel_type)[1]
                    else:
                        main_rel_type = rel_type
                        sec_rel_type = ""
                    rel = {"text_a": text_uri,
                           "code": main_rel_type,
                           "subtype_code": sec_rel_type,
                           "text_b": rel_text}
                    text_relations.append(rel)
                    if not rel in  text_rel_d[text_uri]:
                        text_rel_d[text_uri].append(rel)
                    if not rel in text_rel_d[rel_text]:
                        text_rel_d[rel_text].append(rel)

    # - bibliography:
    bibliography = ""
    bib_fields = ["80#BOOK#EDITIONS#:", "80#BOOK#LINKS####:", "80#BOOK#MSS######:", 
                  "80#BOOK#STUDIES##:", "80#BOOK#TRANSLAT#"]
    field_names = ["EDITIONS:", "LINKS:", "MANUSCRIPTS:", "STUDIES:", "TRANSLATIONS:"]
    for field in bib_fields:
        if field in text_d and not text_d[field].startswith("permalink"):
            field_name = field_names[bib_fields.index(field)]
            bibliography += "{field_name}:\n{text_d[field]\n}"

    # - notes:
    notes = ""
    if "90#BOOK#COMMENT##:" in text_d:
        if text_d["90#BOOK#COMMENT##:"] and not text_d["90#BOOK#COMMENT##:"].strip().startswith("a free running comment"):
            notes = text_d["90#BOOK#COMMENT##:"].strip()
            notes = re.sub(r"    ", "", notes)
    else:
        print("MISSING KEY: 90#BOOK#COMMENT##: in", text_uri)
        print(json.dumps(text_d, indent=2, ensure_ascii=False))
        input()

    text_meta = dict(
        text_uri=text_uri,
        author_meta="",
        titles_ar=title_ar,  # list; will be joined with list of titles from metadata headers later
        titles_lat=" :: ".join(title_lat),
        title_ar_prefered=title_ar_prefered,
        title_lat_prefered=title_lat_prefered,
        text_type="text",
        tags=tags,
        bibliography=bibliography,
        notes=notes,
        place_relations=place_relations,
        text_relations=text_relations
    )

    return text_meta

def collect_author_yml_data(author_yml_fp, author_uri):
    # collect the author's dates from the URI:
    date_str = author_uri[:4]
    date = int(date_str)
    date_AH = date
    date_CE = ah2ce(date)
    
    # load the author yml file as a dictionary:
    auth_d = readYML(author_yml_fp)

    # create a full name from the name elements:
    name_d = dict()
    shuhra = ""
    full_name = ""
    english_name = ""
    if not ("Fulān" in auth_d["10#AUTH#SHUHRA#AR:"]\
            or "none" in auth_d["10#AUTH#SHUHRA#AR:"].lower()):
        shuhra = auth_d["10#AUTH#SHUHRA#AR:"].strip()
        shuhra_ar = betaCodeToArSimple(shuhra)
    name_comps = ["10#AUTH#LAQAB##AR:",
                  "10#AUTH#KUNYA##AR:",
                  "10#AUTH#ISM####AR:",
                  "10#AUTH#NASAB##AR:",
                  "10#AUTH#NISBA##AR:"]
    full_name = [auth_d[x] for x in name_comps \
                    if x in auth_d \
                    and not ("Fulān" in auth_d[x] \
                                or "none" in auth_d[x].lower())]
    full_name = " ".join(full_name).strip()
    full_name_ar = betaCodeToArSimple(full_name)
    if not shuhra:
        shuhra = full_name
        shuhra_ar = full_name_ar
    name_comps_en = [x.replace("#AR:", "#EN:") for x in name_comps]
    english_name = [auth_d[x] for x in name_comps_en \
                    if x in auth_d and \
                    not ("Fulān" in auth_d[x] \
                            or "none" in auth_d[x].lower())]
    english_name = " ".join(english_name).strip()

    name_from_uri = re.sub("([A-Z])", r" \1", author_uri).strip()
    name_from_uri = name_from_uri.replace("c", "ʿ").replace("C", "ʿ")

    # collect author name elements:
    present_languages = []
    for key in auth_d:
        lang = re.findall("#([A-Z]{2}):", key)
        if lang and lang[0] not in present_languages and lang[0] not in ["AH", "CE"]:
            present_languages.append(lang)
    #for lang in ["AR", "EN", "FA"]:
    for lang in present_languages:
        lang_d = dict()
        add = False
        for yml_k in ["10#AUTH#SHUHRA#AR:"]+name_comps:
            yml_k = yml_k.replace("#AR:", "#{}:".format(lang))
            k = re.findall("(?<=10#AUTH#)\w+", yml_k)[0].lower()
            lang_d[k] = get_name_el(auth_d, yml_k)
            if lang_d[k]:
                add = True
        if add:
            if lang == "EN":
                name_d[lang] = lang_d
            else:
                # store a version of the name in transcription and Arabic script:
                name_d["LA"] = lang_d
                lang_d_converted = {k: betaCodeToArSimple(v) for k,v in lang_d.items()}
                name_d[lang] = lang_d_converted


    # geo data:
    geo_regex = r"\w+_RE(?:_\w+)?|\w+_[RSNO]\b|\w+XXXYYY\w*"
    place_relations = []
    
    born = re.findall(geo_regex, auth_d["20#AUTH#BORN#####:"])
    for p in born:
        place_relations.append(dict(code="BORN", subtype_code="", person_a=author_uri, place_b=p))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
        
    died = re.findall(geo_regex, auth_d["20#AUTH#DIED#####:"])
    for p in died:
        place_relations.append(dict(code="DIED", subtype_code="", person_a=author_uri, place_b=p))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
    
    resided = re.findall(geo_regex, auth_d["20#AUTH#RESIDED##:"])
    for p in resided:
        place_relations.append(dict(code="RESID", subtype_code="", person_a=author_uri, place_b=p))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
    
    visited = re.findall(geo_regex, auth_d["20#AUTH#VISITED##:"])
    for p in visited:
        place_relations.append(dict(code="VISIT", subtype_code="", person_a=author_uri, place_b=p))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)

    # person_relations:
    person_relations = []
    if "40#AUTH#STUDENTS#:" in auth_d:
        if not "from OpenITI" in auth_d["40#AUTH#STUDENTS#:"]:
            for student in auth_d["40#AUTH#STUDENTS#:"].split(","):
                student_uri = re.findall("\d{4}[A-Z][a-zA-Z]+", student)
                if student_uri:
                    if not student.strip() == student_uri[0]:
                        print("Additional information in student field?", student)
                    person_relations.append(dict(code="STUD", subtype_code="", person_a=student_uri[0], person_b=author_uri))
    else:
        print("MISSING KEY 40#AUTH#STUDENTS# in", author_uri)
        print(json.dumps(auth_d, indent=2, ensure_ascii=False))
        input()
    if not "from OpenITI" in auth_d["40#AUTH#TEACHERS#:"]:
        for teacher in auth_d["40#AUTH#TEACHERS#:"].split(","):
            teacher_uri = re.findall("\d{4}[A-Z][a-zA-Z]+", teacher)
            if teacher_uri:
                if not re.sub("[\s¶]+", "", teacher) == teacher_uri[0]:
                    print("Additional information in teacher field?", teacher)
                person_relations.append(dict(code="STUD", subtype_code="", person_a=author_uri, person_b=teacher_uri[0]))

    # collect bibliography:
    bibliography = ""
    if auth_d["80#AUTH#BIBLIO###:"] and not auth_d["80#AUTH#BIBLIO###:"].strip().startswith("src@id"):
        bibliography = auth_d["80#AUTH#BIBLIO###:"].strip()
        bibliography = re.sub(r"\s+", " ", bibliography)

    # collect notes:
    notes = ""
    if "90#AUTH#COMMENT##:" in auth_d:
        if auth_d["90#AUTH#COMMENT##:"] and not auth_d["90#AUTH#COMMENT##:"].strip().startswith("a free running comment"):
            notes = auth_d["90#AUTH#COMMENT##:"].strip()
            notes = re.sub(r"    ", "", notes)
    else:
        print("MISSING KEY: 90#AUTH#COMMENT##: in", author_uri)
        print(json.dumps(auth_d, indent=2, ensure_ascii=False))
        input()

    author_meta = dict(
        author_uri=author_uri,
        author_ar=" :: ".join([x for x in [shuhra_ar, full_name_ar] if x]),
        author_lat=" :: ".join([x for x in [shuhra, full_name, english_name, name_from_uri] if x]),
        author_ar_prefered=shuhra_ar,
        author_lat_prefered=shuhra,
        date=date,
        date_AH=date_AH,
        date_CE=date_CE,
        date_str=date_str,
        tags="",
        notes=notes,
        name_elements=name_d,
        place_relations=place_relations,
        person_relations=person_relations,
        bibliography=bibliography
        )
    return author_meta

def read_header(fp):
    """Read only the OpenITI header of a file without opening the entire file.

    Args:
        fp (str): path to the text file

    Returns:
        header (list): A list of all metadata lines in the header
    """
    with open(fp, mode="r", encoding="utf-8") as file:
        header = []
        line = file.readline()
        i=0
        while "#META#Header#End" not in line and i < 100:
            if "#META#" in line or "#NewRec#" in line:
                header.append(line)
            line = file.readline() # move to next line
            i += 1
    return header


def extract_metadata_from_header(fp):
    """Extract the metadata from the headers of the text files.

    Args:
        fp (str): path to the text file

    Returns:
        meta (dict): dictionary containing relevant extracted header items
    """
    header = read_header(fp)
    categories = "AuthorName Title Date Genre "
    categories += "Edition:Editor Edition:Publisher Edition:Place Edition:Date"
    meta = {x : [] for x in categories.split()}
    unreadable = []
    all_meta = dict()
    
    for line in header:
        split_line = line[7:].split("\t::")  # [7:] : start reading after #META# tag
        if len(split_line) == 1:
            split_line = line[7:].split(": ", 1)  # split after first colon
        if len(split_line) > 1:
            val = split_line[1].strip()
            if val.startswith("NO"):
                val = ""
            else:
                # remove line endings within heading categories: 
                val = re.sub(" +", "@@@", val)
                val = re.sub("\s+", "¶ ", val)
                val = re.sub("@@@", " ", val).strip()
                if val.isnumeric():
                    val = str(int(val))
            if val != "":
                key = re.sub("\# ", "", split_line[0])
                all_meta[key] = val
                # reorganize the relevant headers under overarching categories:
                if key in headings_dict:
                    cat = headings_dict[key]
                    val = re.sub("¶.+", "", val)
                    meta[cat].append(val)
        else:
            unreadable.append(line)
    if VERBOSE:
        if unreadable:
            print(fp, "METADATA IN UNREADABLE FORMAT")
            for line in unreadable:
                print(line)
            print(meta)
            input("press enter to continue")

    
    all_header_meta[os.path.split(fp)[0]] = all_meta
    return meta

def insert_spaces(s):
    """Split the camel-case string s and insert a space before each capital."""
    return re.sub("([a-z])([A-Z])", r"\1 \2", s)

def get_name_el(d, k):
    if k in d:
        if not "fulān" in d[k].lower() and not "none" in d[k].lower():
            return d[k]
    return ""