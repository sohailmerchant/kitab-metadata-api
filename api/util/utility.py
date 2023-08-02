"""Utility functions and constants for use in commands scripts"""

import json
import os
import re

from openiti.helper.ara import deNoise, ar_cnt_file
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from api.util.betaCode import betaCodeToArSimple

geo_URIs = dict()
text_rel_d = dict()



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


def ah2ce(date):
    """convert AH date to CE date"""
    return 622 + (int(date) * 354 / 365.25)


def ce2ah(date):
    """convert CE date to AH date"""
    return (int(date) - 622) * 365.25 / 354

def insert_spaces(s):
    """Split the camel-case string s and insert a space before each capital."""
    return re.sub("([A-Z])", r" \1", s).strip()

def replace_c_with_cayn(s):
    """Replace the c in an OpenITI URI string with ʿAyn"""
    # lower-case: simply replace c with ʿayn
    s = s.replace("c", "ʿ") 
    # upper-case: make the next letter upper case!
    s = re.sub("C([a-z])", lambda match: "ʿ"+match.group(1).upper(), s)
    return s

def get_name_el(d, k):
    """Get the name element (shuhra, kunya, ...) from an OpenITI author yml dict
    (returning an empty string if the yml dict contains the default value
    
    Args:
        d (dict): a dictionary generated from an OpenITI author yml file
        k (str): a key of a specific name element (shuhra, kunya, ...) in the author yml dictionary

    Returns:
        str
    """
    if k in d:
        if not "fulān" in d[k].lower() and not "none" in d[k].lower():
            return d[k]
    return ""


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

def tags2dic(tags_fp):
    """Load tags from the tags/genre file created by Maxim into a dictionary
    
    NB: These tags are organized by version ID but are mostly text-related, not version-related
    """
    with open(tags_fp, "r", encoding="utf8") as f1:
        dic = {}
        data = f1.read().split("\n")

        for d in data:
            version_code, tags = d.split("\t")
            dic[version_code] = tags.split(";")
    return dic

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


def extract_metadata_from_header(fp, VERBOSE=False):
    """Extract the metadata from the metadata header of a text file.

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

    
    #all_header_meta[os.path.split(fp)[0]] = all_meta
    return meta



def collect_version_yml_data(version_yml_fp, version_uri, corpus_folder, base_url):
    """Collect all metadata from an OpenITI version yml file
    
    Args:
        version_yml_fp (str): path to a (local) OpenITI version yml file
        version_uri (str): OpenITI version URI
        corpus_folder (str): path to the (local) folder containing the 25AH year OpenITI corpus folders
        base_url (str): URL on raw.githubusercontents that serves the raw files 
            for the relevant release/current state of the corpus

    Returns:
        tuple (version_fp: str, version_meta: dict)
    """

    version_code = version_uri.split("-")[0].split(".")[-1]
    language = version_uri.split("-")[1][:3]
    try:
        collection_code = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", version_code)[0]
    except:
        print("no collection code found in", version_code)
        collection_code = None
        input("CONTINUE?")

    vers_d = readYML(version_yml_fp)

    # - explicit primary version:

    primary_yml = ""
    if "PRIMARY_VERSION" in vers_d["90#VERS#ISSUES###:"]:
        primary_yml = "pri"
    else:
        primary_yml = "sec"

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

    url = version_fp.replace(corpus_folder, base_url).replace("\\","/")
    url = url.replace("AH/data", "AH/master/data")

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
        with open(version_yml_fp, mode="w", encoding="utf-8") as file:
            file.write(ymlS)

    # - edition_link:

    worldcat_url = ""
    if "80#VERS#BASED####:" in vers_d:
        if vers_d["80#VERS#BASED####:"] and not vers_d["80#VERS#BASED####:"].strip().startswith("permalink"):
            worldcat_url = vers_d["80#VERS#BASED####:"].strip()
            worldcat_url = re.sub(r"[\s¶]*,[\s¶]", ",", worldcat_url)
    else:
        print("MISSING KEY: 80#VERS#BASED####: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        input()
    
    pdf_url = ""
    if "80#VERS#LINKS####:" in vers_d:
        if vers_d["80#VERS#LINKS####:"] and not vers_d["80#VERS#LINKS####:"].strip().startswith("all@id"):
            pdf_url = vers_d["80#VERS#LINKS####:"].strip()
            pdf_url = re.sub(r"[\s¶]*,[\s¶]", ",", pdf_url)
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
        print("MISSING KEY: 90#VERS#COMMENT##: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        input()

    # - issues: 
    version_tags = re.findall("[A-Z_]{5,}", vers_d["90#VERS#ISSUES###:"])

    version_meta = dict(
        # version_meta:
        version_code=version_code,
        version_uri=version_uri,
        collection_code=collection_code,
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
        worldcat_url=worldcat_url,
        pdf_url=pdf_url
    )

    return version_fp, version_meta


def collect_text_yml_data(text_yml_fp, text_uri):
    """Collect all metadata from an OpenITI text yml file
    
    Args:
        text_yml_fp (str): path to an OpenITI text yml file
        text_uri (str): an OpenITI text URI
    
    Returns:
        dict
    """
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
    title_from_uri = text_uri.split(".")[1]
    title_from_uri = insert_spaces(title_from_uri)
    title_from_uri = replace_c_with_cayn(title_from_uri)
    #title_from_uri = re.sub("([A-Z])", r" \1", text_uri.split(".")[1]).strip()
    #title_from_uri = title_from_uri.replace("c", "ʿ")
    #title_from_uri = re.sub("C([a-z])", lambda match: "ʿ"+match.group(1).upper(), title_from_uri)
    
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
    person_relations = []
    if not "40#BOOK#RELATED##:" in text_d:
        print("MISSING KEY 40#BOOK#RELATED##: in", text_uri)
    else:
        if text_d["40#BOOK#RELATED##:"].strip() and not text_d["40#BOOK#RELATED##:"].strip().startswith("URI of"):
            # get the book relations string and split it into relations (rels):
            rels = text_d["40#BOOK#RELATED##:"].strip()
            rels = re.sub(" *[\r\n¶]+ *", " ", rels)
            rels = re.split(" *[;:]+ *", rels)

            # add each relation to the relevant list:
            for rel in rels:
                rel = re.sub(" +", " ", rel)
                if "@" in rel:  # new format: COMM.sharh@0255Jahiz.Hayawan
                    rel_types = rel.split("@")[0]
                    rel_text = rel.split("@")[1]
                else:           # old format: 0255Jahiz.Hayawan (COMM.sharh)
                    try:
                        rel_types = re.findall("\(([^\)]+)", rel)[0]
                    except:
                        print(text_uri, ":")
                        print("    no relationship type found in ", rel)
                        continue
                    rel_text = re.sub(" *\(.+", "", rel).strip()
                
                # prepare to store the relations in both directions
                if not text_uri in text_rel_d:
                    text_rel_d[text_uri] = []
                if not rel_text in text_rel_d:
                    text_rel_d[rel_text] = []

                # 
                for rel_type in re.split(" *, *", rel_types):
                    if "." in rel_type:
                        main_rel_type = re.split(" *\. *", rel_type)[0]
                        sec_rel_type = re.split(" *\. *", rel_type)[1]
                    else:
                        main_rel_type = rel_type
                        sec_rel_type = ""
                    rel = {"text_a": text_uri,
                           "code": main_rel_type,
                           "subtype_code": sec_rel_type
                           }
                    if rel_text.count(".") == 0:  # AUTHOR URI instead of text URI!
                        rel["person_b"] = rel_text
                        person_relations.append(rel)
                    else:
                        rel["text_b"] = rel_text
                        text_relations.append(rel)
                    # store ther relation in both directions in the dictionary (not used later)
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
        text_relations=text_relations,
        person_relations=person_relations
    )

    return text_meta



def collect_author_yml_data(author_yml_fp, author_uri):
    """Collect all metadata from an OpenITI author yml file"""
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

    name_from_uri = author_uri[4:]
    name_from_uri = insert_spaces(name_from_uri)
    name_from_uri = replace_c_with_cayn(name_from_uri)
    #name_from_uri = re.sub("([A-Z])", r" \1", author_uri[4:]).strip()
    #name_from_uri = name_from_uri.replace("c", "ʿ").replace("C", "ʿ")

    # collect author name elements:
    present_languages = []
    for key in auth_d:
        lang = re.findall("#([A-Z]{2}):", key)
        if lang and lang[0] not in present_languages and lang[0] not in ["AH", "CE"]:
            present_languages.append(lang[0])
    #print(present_languages)
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
                    person_relations.append(dict(code="STUDENT", subtype_code="", person_a=student_uri[0], person_b=author_uri))
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
                person_relations.append(dict(code="STUDENT", subtype_code="", person_a=author_uri, person_b=teacher_uri[0]))

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

    try:
        author_ar_prefered = [x for x in [shuhra_ar, full_name_ar] if x][0]
    except:
        author_ar_prefered = ""
    author_lat_prefered=[x for x in [shuhra, full_name, english_name, name_from_uri] if x][0]

    author_meta = dict(
        author_uri=author_uri,
        author_ar=" :: ".join([x for x in [shuhra_ar, full_name_ar] if x]),
        author_lat=" :: ".join([x for x in [shuhra, full_name, english_name, name_from_uri] if x]),
        author_ar_prefered=author_ar_prefered,
        author_lat_prefered=author_lat_prefered,
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


def set_analysis_priority(version_list):
    """Check which of the versions of the text should get primary status
    
    Args:
        version_list (list): list of version_meta dictionaries
    """
    # do not process empty version lists:
    if len(version_list) < 1:
        return version_list
    # if there's only one version, it should automatically be the primary version:
    if len(version_list) == 1:
        version_list[0]["analysis_priority"] = "pri"
    # if one or more texts already have primary status because of a flag in the yml file: stick to that:
    if "pri" in [d["analysis_priority"] for d in version_list]:
        return version_list
    else:
        # check if any text has a more advanced annotation status than the others; if so, pick that one as primary text:
        annotation_statuses = [d["annotation_status"] for d in version_list]
        if "mARkdown" in annotation_statuses:
            mARkdown_indexes = [i for i, status in enumerate(annotation_statuses) if status=="mARkdown"]
            for i in mARkdown_indexes:
                version_list[i]["analysis_priority"] = "pri"
            return version_list
        elif "completed" in annotation_statuses:
            completed_indexes = [i for i, status in enumerate(annotation_statuses) if status=="completed"]
            for i in completed_indexes:
                version_list[i]["analysis_priority"] = "pri"
            return version_list
        else:
            # sort the version list by length of the text (from long to short):
            version_list = sorted(version_list, key=lambda el:int(el["char_length"]), reverse=True)
            # take the longest text as primary text:
            version_list[0]["analysis_priority"] = "pri"
            return version_list