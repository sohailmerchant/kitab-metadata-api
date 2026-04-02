"""Utility functions and constants for use in commands scripts"""

import copy
import json
import os
import re
import datetime
import logging
import convertdate


from openiti.git import get_issues
from openiti.helper.ara import deNoise, ar_cnt_file
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from api.util.betacode import betacodeToArSimple, betacodeToSearch

geo_URIs = dict()
text_rel_d = dict()

# prepare logger: 
today = datetime.datetime.today().strftime("%Y-%m-%d")
log_fp = f'logs/release_upload_{today}.log'
if os.path.exists(log_fp):
    with open(log_fp, mode="w", encoding="utf-8") as file:
        file.write("")
logging.basicConfig(filename=log_fp, encoding='utf-8', level=logging.NOTSET)
logger = logging.getLogger()


DATE_CONVERTERS  = {
    "AH": convertdate.islamic,
    "hijri": convertdate.islamic,
    "qamari": convertdate.islamic,
    "shamsi": convertdate.persian,
    "persian": convertdate.persian,
    "coptic": convertdate.coptic,
    "armenian": convertdate.armenian,
    "hebrew": convertdate.hebrew
}

ARABIC_SCRIPT_CODES = ["AR", "FA", "PE", "UR", "ARA", "PER", "FAR", "URD"]

# Create a lookup dictionary for the country codes:
# source: https://gist.githubusercontent.com/anubhavshrimal/75f6183458db8c453306f93521e93d37/raw/f77e7598a8503f1f70528ae1cbf9f66755698a16/CountryCodes.json
with open("meta/CountryCodes.json", encoding="utf-8") as file:
    data = json.load(file)
    COUNTRY_CODES = dict()
    for d in data:
        n = int(re.sub(r"\D+", "", d["dial_code"]))
        code = f"{n:04d}"
        if code not in COUNTRY_CODES:
            COUNTRY_CODES[code] = {"name": d["name"], "db_object": None}
        else:
            COUNTRY_CODES[code]["name"] += "; " + d["name"]



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

def to_datetime(gregorian_tuple):
    """
    convertdate.<cal>.to_gregorian returns (year, month, day) tuples.
    Convert to datetime.date.
    """
    if not gregorian_tuple:
        return None
    y, m, d = gregorian_tuple
    return datetime.date(int(y), int(m), int(d))

def normalize_precision(precision, month, day):
    """
    precision can be: "year", "month", "day" or whatever you store.
    If missing/invalid, infer from the presence/absence of month/day.
    """
    if precision in ("year", "month", "day"):
        return precision
    if not month:
        return "year"
    if not day:
        return "month"
    return "day"

def compute_ce_range(calendar, year, month=None, day=None, precision=None):
    """
    Compute (ce_start, ce_end) as datetime.date objects from a calendar date.

    Args:
        calendar (str): "gregorian", "hijri", "persian", ...
        year (int): the year value
        month (int): the month value
        day (int): the day value
        precision (str): "millennium" | "century" | "year" | "month" | "day"; if None, the precision
            will be inferred from the presence/absence of month and day values

    Returns:
        (datetime, datetime)
    """
    if year is None:
        return (None, None)

    if calendar in ("gregorian", "CE", "BCE"):
        return compute_ce_range_from_gregorian(year, 
            month=month, day=day, precision=precision)

    return compute_ce_range_from_other_calendar(calendar, year, 
            month=month, day=day, precision=precision)

def compute_ce_range_from_gregorian(year, month=None, day=None, precision=None):
    """
    Compute (ce_start, ce_end) as datetime.date objects from a CE calendar date.

    Args:
        year (int): the year value
        month (int): the month value
        day (int): the day value
        precision (str): "millennium" | "century" | "decennium" | "year" | "month" | "day"; if None, the precision
            will be inferred from the presence/absence of month and day values
    
    Returns:
        (datetime, datetime)
    """
    if year is None:
        return (None, None)

    precision = normalize_precision(precision, month, day)

    if precision == "millennium":
       return (datetime.date(year, 1, 1), datetime.date(year+999, 12, 31))

    if precision == "century":
       return (datetime.date(year, 1, 1), datetime.date(year+99, 12, 31))

    if precision == "decennium":
       return (datetime.date(year, 1, 1), datetime.date(year+9, 12, 31))

    if precision == "year":
        return (datetime.date(year, 1, 1), datetime.date(year, 12, 31))

    if precision == "month" and month:
        start = datetime.date(year, month, 1)
        if month == 12:
            end = datetime.date(year, 12, 31)
        else:
            end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        return (start, end)

    if precision == "day" and month and day:
        d = datetime.date(year, month, day)
        return (d, d)

    return (None, None)


def compute_ce_range_from_other_calendar(calendar, year, month=None, day=None, precision=None):
    """
    Compute (ce_start, ce_end) as datetime.date objects from a non-CE calendar date.
    
    Uses convertdate.* converters. 

    Args:
        calendar (str): "gregorian", "hijri", "persian", ...
        year (int): the year value
        month (int): the month value
        day (int): the day value
        precision (str): "year" | "month" | "day"; if None, the precision
            will be infrerred from the presence/absence of month and day values
    
    Returns:
        (datetime, datetime)
    """
    if year is None:
        return (None, None)

    converter = DATE_CONVERTERS.get(calendar)
    if converter is None:
        print("UNKNOWN CALENDAR:", calendar)
        return (None, None)

    precision = normalize_precision(precision, month, day)

    if precision == "millennium":
        start = to_datetime(converter.to_gregorian(year, 1, 1))
        last_year = year+999
        last_month = 12
        try:
            last_day = converter.month_length(last_year, last_month)
        except Exception:
            last_day = 30 # approximation

        end = to_datetime(converter.to_gregorian(last_year, last_month, last_day))
        return (start, end)

    if precision == "century":
        start = to_datetime(converter.to_gregorian(year, 1, 1))
        last_year = year+99
        last_month = 12
        try:
            last_day = converter.month_length(last_year, last_month)
        except Exception:
            last_day = 30 # approximation

        end = to_datetime(converter.to_gregorian(last_year, last_month, last_day))
        return (start, end)

    if precision == "decennium":
        start = to_datetime(converter.to_gregorian(year, 1, 1))
        last_year = year+9
        last_month = 12
        try:
            last_day = converter.month_length(last_year, last_month)
        except Exception:
            last_day = 30 # approximation

        end = to_datetime(converter.to_gregorian(last_year, last_month, last_day))
        return (start, end)

    # YEAR precision: whole year in that calendar
    if precision == "year":
        start = to_datetime(converter.to_gregorian(year, 1, 1))

        # last day of last month of the year, in that calendar
        # (convertdate modules generally provide month_length)
        last_month = 12
        try:
            last_day = converter.month_length(year, last_month)
        except Exception:
            last_day = 30 # approximation

        end = to_datetime(converter.to_gregorian(year, last_month, last_day))
        return (start, end)

    # MONTH precision: whole month in that calendar
    if precision == "month" and month:
        start = to_datetime(converter.to_gregorian(year, month, 1))
        try:
            last_day = converter.month_length(year, month)
        except Exception:
            last_day = 30 # approximation
        end = to_datetime(converter.to_gregorian(year, month, last_day))
        return (start, end)

    # DAY precision: specific day
    if precision == "day" and month and day:
        d = to_datetime(converter.to_gregorian(year, month, day))
        return (d, d)

    return (None, None)

def insert_spaces(s):
    """Split the camel-case string s and insert a space before each capital."""
    s = re.sub(r"([A-Z])", r" \1", s).strip()
    s = re.sub(" Wa ", " wa-", s)
    return s

def replace_c_with_cayn(s):
    """Replace the c in an OpenITI URI string with ʿAyn"""
    # first, make sure Cs are not replaced in English words:
    if re.findall("comp|comm|anonym", s.lower()):
        return s
    # lower-case: simply replace c with ʿayn
    s = s.replace("c", "ʿ") 
    # upper-case: make the next letter upper case!
    s = re.sub(r"C([a-z])", lambda match: "ʿ"+match.group(1).upper(), s)
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
    start_year = re.sub(r"[Xx]", "0", year)
    end_year = re.sub(r"[Xx]", "9", year)
    if re.findall(r"[Xx]", month):
        start_month = "01"
        end_month = "12"
    else:
        try:
            start_month = lunar_months[month]
            end_month = lunar_months[month]
        except:
            start_month = month
            end_month = month
    start_day = re.sub(r"[Xx]", "0", day)
    end_day = re.sub(r"[Xx]", "9", day)
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
                val = re.sub(r" +", "@@@", val)
                val = re.sub(r"\s+", "¶ ", val)
                val = re.sub(r"@@@", " ", val).strip()
                if val.isnumeric():
                    val = str(int(val))
            if val != "":
                key = re.sub(r"\# ", "", split_line[0])
                all_meta[key] = val
                # reorganize the relevant headers under overarching categories:
                if key in headings_dict:
                    cat = headings_dict[key]
                    val = re.sub(r"¶.+", "", val)
                    meta[cat].append(val)
        else:
            unreadable.append(line)
    if VERBOSE:
        if unreadable:
            print(fp, "METADATA IN UNREADABLE FORMAT")
            for line in unreadable:
                print(line)
            print(meta)
            #input("press enter to continue")

    
    #all_header_meta[os.path.split(fp)[0]] = all_meta
    return meta



def collect_version_yml_data(vers_d, base_url, corpus_folder=None, 
                             version_yml_fp=None, recalculate=False):
    """Collect all metadata from an OpenITI version yml file
    
    Args:
        vers_d (dict): version yml dictionary
        corpus_folder (str): path to the (local) folder containing the 25AH year OpenITI corpus folders
        base_url (str): URL on raw.githubusercontents that serves the raw files 
            for the relevant release/current state of the corpus

    Returns:
        version_meta: dict
    """
    # - version URI and derived variables:
    version_uri = vers_d["00#VERS#URI######:"]
    version_code = version_uri.split("-")[0].split(".")[-1]
    languages = re.findall(r"[a-z]{3}", version_uri.split("-")[1])
    language = ",".join(languages)
    try:
        #collection_code = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", version_code)[0]
        collection_code = re.findall(r"^[A-Za-z]+?\d{,2}[A-Za-z]+", version_code)[0]
    except:
        msg = f"no collection code found in '{version_code}'"
        logger.warning(msg)
        print(msg)
        collection_code = None
        #input("CONTINUE?")

    # - explicit primary version:

    primary_yml = ""
    if "PRIMARY_VERSION" in vers_d["90#VERS#ISSUES###:"]:
        primary_yml = "pri"
    else:
        primary_yml = "sec"

    # - most developed text version:

    if "path" in vers_d:
        pth = vers_d["path"]
    else:
        pth = version_yml_fp[:-4]
    extensions = [".mARkdown", ".completed", ".inProgress", ""]
    for ext in extensions:
        if "extensions" in vers_d:
            if ext in vers_d["extensions"]:
                version_fp = pth + ext
                break
        else:
            version_fp = pth + ext
            if os.path.exists(version_fp):
                break
        # if even the path with no extension does not exist:
        if ext == "":
            version_fp = ""
            print("NO TEXT VERSION FOUND FOR THIS YML FILE:", version_yml_fp)

    # - url:
    if corpus_folder: # data in 25Y folders
        url = version_fp.replace(corpus_folder, base_url).replace("\\","/")
        #url = url.replace("AH/data", "AH/master/data")
    else:
        url = base_url.strip("/") + "/" + version_fp
        #url = url.replace("/data/", "/master/data/")

    # annotation status:

    if not ext:
        annotation_status = "(not yet annotated)"
    else:
        annotation_status = ext[1:]

    # - length in number of characters and (Arabic-script) tokens:

    tok_length = vers_d["00#VERS#LENGTH###:"].strip()
    char_length = vers_d["00#VERS#CLENGTH##:"].strip()

    # recalculate the length if it is not present in the yml file:
    if recalculate and not (tok_length and char_length):
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
    based_list = parse_val_as_list(vers_d, "80#VERS#BASED####:", 
                                   default_start="permalink,")
    external_ids = {}
    for based_url in based_list:
        org_regex = r"^(?:https?://)?(?:www\.)?(?:[a-z]{2}\.)?(\w+)"
        org = re.findall(org_regex, based_url.strip())
        if org:
            org = org[0]
        else:
            org = "NA"
        if org not in external_ids:
            external_ids[org] = []
        external_ids[org].append(based_url)
    worldcat_links = [v for k, v in external_ids.items() if k.lower() == "worldcat"]
    if "worldcat" in external_ids:
        del external_ids["worldcat"]
    elif "Worldcat" in external_ids:
        del external_ids["Worldcat"]
    # external_ids = {}
    # if "80#VERS#BASED####:" in vers_d:
    #     based_raw = vers_d["80#VERS#BASED####:"].strip()
    #     if based_raw and not based_raw.startswith("permalink"):
    #         for url in re.split(r"[\s¶]*[,;:]+[\s¶]", based_raw):
    #             org_regex = r"^(?:https?://)?(?:www\.)?(?:[a-z]{2}\.)?(\w+)"
    #             org = re.findall(org_regex, url.strip())
    #             if org:
    #                 org = org[0]
    #             else:
    #                 org = "NA"
    #             if org not in external_ids:
    #                 external_ids[org] = []
    #             external_ids[org].append(url)
    # else:
    #     print("MISSING KEY: 80#VERS#BASED####: in", version_uri)
    #     print(json.dumps(vers_d, indent=2, ensure_ascii=False))
    #     input()
    
    pdf_url = ""
    if "80#VERS#LINKS####:" in vers_d:
        raw_links = vers_d["80#VERS#LINKS####:"].strip()
        if raw_links and not raw_links.startswith("all@id"):
            pdf_url = re.sub(r"[\s¶]*[,;:]+[\s¶]", ",", raw_links)
    else:
        print("MISSING KEY: 80#VERS#LINKS####: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        #input()

    # - notes:
    notes = ""
    if "90#VERS#COMMENT##:" in vers_d:
        raw_notes = vers_d["90#VERS#COMMENT##:"].strip()
        if raw_notes and not raw_notes.startswith("a free running comment"):
            notes = re.sub(r" +", " ", raw_notes)
    else:
        print("MISSING KEY: 90#VERS#COMMENT##: in", version_uri)
        print(json.dumps(vers_d, indent=2, ensure_ascii=False))
        #input()

    # - issues: 
    #version_tags = re.findall(r"[A-Z_]{5,}", vers_d["90#VERS#ISSUES###:"])
    issues = parse_val_as_str(vers_d, "90#VERS#ISSUES###:",
                              default_start="comma-separated list")
    issues = re.findall(r"[A-Z_]{5,}", issues)

    uncorrected_OCR = False
    if "UNCORRECTED_OCR" in issues:
        uncorrected_OCR=True

    version_meta = dict(
        # version_meta:
        version_code=version_code,
        version_uri=version_uri,
        language=language,
        collection_code=collection_code,
        text_meta="",
        edition_meta="",
        # release_version_meta:
        char_length=char_length,
        tok_length=tok_length,
        path=version_fp,
        url=url,
        analysis_priority=primary_yml,
        annotation_status=annotation_status,
        notes=notes,
        tags=" :: ".join(issues),
        header_meta=vers_d.get("header_meta", {}),
        subcorpus=language,
        uncorrected_OCR=uncorrected_OCR,
        # edition_meta:
        external_ids=external_ids,
        worldcat_links=worldcat_links,
        pdf_url=pdf_url,
    )

    return version_meta


def collect_text_yml_data(text_d, text_uri=None):
    """Collect all metadata from an OpenITI text yml file
    
    Args:
        text_yml_fp (str): path to an OpenITI text yml file
        text_uri (str): an OpenITI text URI
    
    Returns:
        dict
    """
    if not text_uri:
        text_uri = text_d["00#BOOK#URI######:"]

    # - title:
    title_lat = []
    title_ar = []
    title_d = {"LAT": []}
    for k in sorted(text_d.keys()): # TITLEA before TITLEB!
        if "TITLE" in k:
            v = text_d[k].strip()
            if not v or "al-Muʾallif" in v or "none" in v.lower():
                continue
            lang = re.findall(r"([A-Z]+):", k)[0]
            if not lang in title_d:
                title_d[lang] = []
            for title in re.split(r" *[,;:]+ *", v):
                if title:
                    if lang in ["AR", "FA", "UR", "PE", "ARA", "PER", "URD"]:
                        ara_title = betacodeToArSimple(title)
                        title_ar.append(ara_title)
                        title_d[lang].append(ara_title)
                        title_d["LAT"].append(title)
                    else:
                        title_d[lang].append(title)
                    title_lat.append(title)

    title_from_uri = text_uri.split(".")[1]
    title_from_uri = insert_spaces(title_from_uri)
    title_from_uri = replace_c_with_cayn(title_from_uri)
    title_lat.append(title_from_uri)
    
    if "title_from_text_header" in text_d:
        ttl = text_d["title_from_text_header"]
        if type(ttl) == str:
            ttl = re.split(r" *[,:;]+ *", ttl)
        for t in ttl:
            t = t.strip()
            if not t:
                continue
            if re.findall("[ء-ي]", t):
                if t not in title_ar:
                    title_ar.append(t)
            else:
                if t not in title_lat:
                    title_lat.append(t)

    normalized_title_lat = [betacodeToSearch(t) for t in title_lat if t]
    
    title_lat_prefered = title_lat[0]
    if title_ar:
        title_ar_prefered = title_ar[0]
    else: 
        title_ar_prefered = ""

    # - tags
    tags = parse_val_as_list(text_d, "10#BOOK#GENRES###:", default_start="src")
    # tags = []
    # raw_tags = text_d["10#BOOK#GENRES###:"].strip()
    # if raw_tags and not raw_tags.startswith("src"):
    #     for genre in re.split(r" *[,:;]+ *", raw_tags):
    #         tags.append(genre)
    tags += text_d.get("genre_from_text_header", [])

    # - place of writing:
    places = parse_val_as_list(text_d, "20#BOOK#WROTE####:", 
                               default_start="URIs from Althurayya")
    # places = []
    # raw_places = text_d["20#BOOK#WROTE####:"].strip()
    # if raw_places and not raw_places.startswith("URIs from Althurayya"):
    #     for place in re.split(r" *[:,;]+ *", raw_places):
    #         places.append(place)

    # - date of writing:
    dates = parse_modifier_vals(text_d, "WROTE#+[A-Z]+#*:", 
                                default_start="YEAR-MON-DA", output="tuples")
    # dates = []
    # for k in text_d:
    #     if "WROTE" in k and "#WROTE####:" not in k:
    #         #raw_dates = text_d["30#BOOK#WROTE##AH:"].strip()
    #         calendar = re.findall(r"([A-Z]+):", k)[0]
    #         raw_dates = text_d[k].strip()
    #         if raw_dates and not raw_dates.startswith("YEAR-MON-DA"):
    #             for date in re.split(r" *[:,;]+ *", raw_dates):
    #                 dates.append((date, calendar))

    # connect place and date of writing:
    place_relations = []
    if places:
        if len(dates) <= len(places):
            for i, place in enumerate(places):
                try:
                    date, calendar = dates[i]
                except:
                    date = ""
                    calendar = ""
                start, end = date_from_string(date)
                place_relations.append(dict(
                    text_a=text_uri, 
                    code="WRITTEN", 
                    subtype_code="", 
                    place_b=place, 
                    date=date,
                    calendar=calendar
                ))
        else:
            for i, date_tup in enumerate(dates):
                date, calendar = date_tup
                try:
                    place = places[i]
                except:
                    place = "UNDEFINED"
                place_relations.append(dict(
                    text_a=text_uri, 
                    code="WRITTEN", 
                    subtype_code="",
                    place_b=place, 
                    date=date,
                    calendar=calendar
                ))


    # - text relations:
    text_relations = []
    person_relations = []
    if not "40#BOOK#RELATED##:" in text_d:
        print("MISSING KEY 40#BOOK#RELATED##: in", text_uri)
    else:
        raw_rels = text_d["40#BOOK#RELATED##:"].strip()
        if raw_rels and not raw_rels.startswith("URI of"):
            # get the book relations string and split it into relations (rels):
            rels = re.sub(r" *[\r\n¶]+ *", " ", raw_rels)
            rels = re.split(r" *[;:]+ *", rels)

            # add each relation to the relevant list:
            for rel in rels:
                rel = re.sub(r" +", " ", rel)
                if "@" in rel:  # new format: COMM.sharh@0255Jahiz.Hayawan
                    rel_types = rel.split("@")[0]
                    rel_text = rel.split("@")[1]
                else:           # old format: 0255Jahiz.Hayawan (COMM.sharh)
                    try:
                        rel_types = re.findall(r"\(([^\)]+)", rel)[0]
                    except:
                        msg = f"{text_uri}: no relationship type found in '{rel}'"
                        logger.warning(msg)
                        print(msg)
                        continue
                    rel_text = re.sub(r" *\(.+", "", rel).strip()
                
                # prepare to store the relations in both directions
                if not text_uri in text_rel_d:
                    text_rel_d[text_uri] = []
                if not rel_text in text_rel_d:
                    text_rel_d[rel_text] = []

                # 
                for rel_type in re.split(r" *, *", rel_types):
                    if "." in rel_type:
                        main_rel_type = re.split(r" *\. *", rel_type)[0]
                        sec_rel_type = re.split(r" *\. *", rel_type)[1]
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
                    elif rel_text.count(".") == 1:
                        rel["text_b"] = rel_text
                        text_relations.append(rel)
                    else:
                        print("Not an author or text URI:", rel_text)
                    # store the relation in both directions in the dictionary
                    if not rel in  text_rel_d[text_uri]:
                        text_rel_d[text_uri].append(rel)
                    if not rel in text_rel_d[rel_text]:
                        text_rel_d[rel_text].append(rel)

    # - external IDs:
    external_ids = get_external_ids(text_d, "70#BOOK#EXTID####:")
    # external_ids = dict()
    # if "70#BOOK#EXTID####:" in text_d:
    #     ext_ids = text_d["70#BOOK#EXTID####:"].strip().lower()
    #     if ext_ids not in ["", "none", "viaf@id, wikidata@id, src@id"]:
    #         for ext_id in re.split(r" *[;,:]+ *", ext_ids):
    #             try:
    #                 src, id_ = ext_id.split("@")
    #             except:
    #                 src = "NA"
    #                 id_ = ext_id
    #             if src not in external_ids:
    #                 external_ids[src] = []
    #             external_ids[src].append(id_)  

    # - bibliography:
    bibliography = ""
    bib_fields = ["80#BOOK#EDITIONS#:", "80#BOOK#LINKS####:", "80#BOOK#MSS######:", 
                  "80#BOOK#STUDIES##:", "80#BOOK#TRANSLAT#"]
    field_names = ["EDITIONS:", "LINKS:", "MANUSCRIPTS:", "STUDIES:", "TRANSLATIONS:"]
    for field in bib_fields:
        if field in text_d and not text_d[field].startswith("permalink"):
            field_name = field_names[bib_fields.index(field)]
            bibliography += "{field_name}:\n{text_d[field]\n}"

    # TODO: process EDITIONS, LINKS, MSS, STUDIES and TRANSLATIONS

    # - notes:
    notes = ""
    if "90#BOOK#COMMENT##:" in text_d:
        raw_notes = text_d["90#BOOK#COMMENT##:"].strip()
        if raw_notes and not raw_notes.startswith("a free running comment"):
            notes = re.sub(r"\s+", " ", raw_notes)
    else:
        print("MISSING KEY: 90#BOOK#COMMENT##: in", text_uri)
        print(json.dumps(text_d, indent=2, ensure_ascii=False))
        #input()

    text_meta = dict(
        text_uri=text_uri,
        author_meta="",
        titles_ar=[t for t in title_ar if t],  # list; will be joined with list of titles from metadata headers later
        titles_lat=" :: ".join(list(set(title_lat + normalized_title_lat))),
        title_ar_prefered=title_ar_prefered,
        title_lat_prefered=title_lat_prefered,
        title_d=title_d,
        text_type="text",
        tags=" :: ".join(tags),
        place_relations=place_relations,
        text_relations=text_relations,
        person_relations=person_relations,
        external_ids=external_ids,
        bibliography=bibliography,
        notes=notes
    )

    return text_meta

def get_city_from_loc_uri(loc_uri):
    if not re.findall(r"^MS\d{4}", loc_uri):
        return ""
    # build the city, character by character,
    # starting from the character after the country code
    city = loc_uri[6]
    for char in loc_uri[7:]:
        if char.isupper(): # start of a new word in the URI
            if city not in ("Los", "St", "Saint", "New", "San", "Al", "El"):
                return city
            city += " "
        city += char
    return ""

def collect_loc_yml_data(loc_d, loc_uri=None):
    if not loc_uri:
        loc_uri = loc_d["00#LOC#URI#######:"].strip()
    
    # process the city and institution names:
    names_d = {"CITY": {}, "INST": {}}
    for k in loc_d:
        try:
            name_type = re.findall("|".join(names_d.keys()), k)[0]
        except: # not a city or institution name key!
            continue
        if "name of" in loc_d[k] or "none" in loc_d[k].lower():
            continue
        _, _, name_type, lang, _ = re.split("#+", k.strip(":"))
        if lang not in names_d[name_type]:
            names_d[name_type][lang] = []
        if lang in ARABIC_SCRIPT_CODES:
            names_d[name_type][lang].append(betacodeToArSimple(loc_d[k]))
        else:
            names_d[name_type][lang].append(loc_d[k])

    # create more legacy name values:
    city_ar = []
    city_lat = []
    for lang in names_d["CITY"]:
        if lang in ARABIC_SCRIPT_CODES:
            for name in names_d["CITY"][lang]:
                city_ar.append(name)
        else:
            for name in names_d["CITY"][lang]:
                city_lat.append(name)
    inst_ar = []
    inst_lat = []
    for lang in names_d["INST"]:
        if lang in ARABIC_SCRIPT_CODES:
            for name in names_d["INST"][lang]:
                inst_ar.append(name)
        else:
            for name in names_d["INST"][lang]:
                inst_lat.append(name)

    
    # TODO: add data from header:
    # if not author_ar and "name_from_text_header" in auth_d:
    #     header_names = auth_d["name_from_text_header"]
    #     for n in re.split(r" *[:;,]+ *", header_names):
    #         if not n.strip():
    #             continue
    #         if re.findall("[ء-ي]", n):
    #             author_ar.append(n.strip())
    #             if not author_ar_prefered:
    #                 author_ar_prefered = n.strip()
    #         else:
    #             author_lat.append(n.strip())
    #             if not author_lat_prefered:
    #                 author_lat_prefered = n.strip()

    # collect external IDs:
    external_ids = get_external_ids(loc_d, "70#LOC#EXTID#####:")
                

    # collect catalogs:
    catalogs = ""
    raw_cat = loc_d["80#LOC#CATALOGS##:"].strip()
    if raw_cat and not raw_cat.startswith("permalink"):
        catalogs = re.sub(r"[\s]+", " ", raw_cat)

    # collect links:
    links = ""
    raw_links = loc_d["80#LOC#LINKS#####:"].strip()
    if raw_links and not raw_links.startswith("WEBSITE@permalink"):
        links = re.sub(r"[\s]+", " ", raw_links)

    # collect notes:
    notes = ""
    if "90#LOC#COMMENT###:" in loc_d:
        raw_notes = loc_d["90#LOC#COMMENT###:"].strip()
        if raw_notes and not raw_notes.startswith("a free running comment"):
            notes = re.sub(r"\s+", " ", raw_notes)
    else:
        print("MISSING KEY: 90#LOC#COMMENT###: in", loc_uri)
        print(json.dumps(loc_d, indent=2, ensure_ascii=False))
        #input()

    loc_meta = dict(
        loc_uri=loc_uri,
        city_names=names_d["CITY"],
        inst_names=names_d["INST"],
        city_ar=" :: ".join(city_ar),
        city_lat=" :: ".join(city_lat),
        institution_ar=" :: ".join(inst_ar),
        institution_lat=" :: ".join(inst_lat),
        external_ids=external_ids,
        catalogs=catalogs,
        links=links,
        notes=notes,
        tags="",
        )
    return loc_meta
    
def parse_val_as_str(d, k, default_start=None, default_return=""):
    """parse the value of a dictionary key as a string. 

    This is to be used when values are separated by a splitter (e.g., "al-Bakrī, al-Baġdādī")

    Examples:
    ```
    >>> d = {"20#AUTH#BORN#####:": "AMUL_524E364N_S :: Daylam_RE"}
    >>> parse_val_as_str(d, "20#AUTH#BORN#####:"}
    "AMUL_524E364N_S :: Daylam_RE"
    >>> d = {"20#AUTH#BORN#####:": "URIs from Althurayya, comma separated"}
    >>> parse_val_as_str(d, "20#AUTH#BORN#####:", default_start="URIs from Althurayya"}
    ''
    ```
    
    Returns:
       str
    """
    try:
        val = d[k].strip()
    except KeyError:
        msg = f"parsing error: key '{k}' not found in {json.dumps(d, ensure_ascii=False)}"
        logger.warning(msg)
        print(msg)
        #return default_return
        return copy.deepcopy(default_return)
    if not val or val.lower() == "none" : 
        #return default_return
        return copy.deepcopy(default_return)
    if default_start and val.startswith(default_start):
        #return default_return
        return copy.deepcopy(default_return)
    return val

def parse_val_as_int(d, k, default_start=None, default_return=0):
    val = parse_val_as_str(d, k, default_start=default_start)
    if not val: 
        #return default_return
        return copy.deepcopy(default_return)
    try: 
        return int(val)
    except:
        msg = f"Expected number in value for key '{k}' in {d}"
        msg += f"Got '{val}'"
        print(msg)
        logger.warning(msg)
        #return default_return
        return copy.deepcopy(default_return)


def parse_val_as_list(d, k, default_start=None, default_return=[], 
                     split_regex=r" *[;,:]+ *"):
    """parse the value of a dictionary key as a list. 

    This is to be used when values are separated by a splitter (e.g., "al-Bakrī, al-Baġdādī")

    Examples:
    ```
    >>> d = {"20#AUTH#BORN#####:": "AMUL_524E364N_S :: Daylam_RE"}
    >>> parse_val_as_list(d, "20#AUTH#BORN#####:"}
    ["AMUL_524E364N_S", "Daylam_RE"]
    >>> d = {"20#AUTH#BORN#####:": "AMUL_524E364N_S, Daylam_RE"}
    >>> parse_val_as_list(d, "20#AUTH#BORN#####:"}
    ["AMUL_524E364N_S", "Daylam_RE"]
    >>> d = {"20#AUTH#BORN#####:": "AMUL_524E364N_S; Daylam_RE"}
    >>> parse_val_as_list(d, "20#AUTH#BORN#####:"}
    ["AMUL_524E364N_S", "Daylam_RE"]
    ```

    Returns:
        list
    """
    # first, get the value as a string:
    val = parse_val_as_str(d, k, default_start=default_start, default_return=default_return)
    if not val:
        #return default_return
        return copy.deepcopy(default_return)
    
    # then, create a list
    vals = []
    if type(val) == str:
        val = re.split(split_regex, val)
    for v in val:
        v = v.strip()
        if v and v not in vals:
            vals.append(v)
    return vals

def parse_val_as_dict(d, k, default_start=None, default_return={}, 
                     split_regex=r" *[;,:]+ *", key_value_splitter="@"):
    """parse the value of a dictionary key as a dictionary. 

    This is to be used when values can take key-value format (e.g., COPIED@Baghad)

    Example:
    ```
    >>> d = {"30#MS#SCRIPT#####:": "ara@naskh, ara@nastacliq"}
    >>> parse_val_as_dict(d, k}
    {"ara": ["naskh", "nastacliq"]}
    ```

    Returns:
        dict
    """
    vals = parse_val_as_list(d, k, default_start=default_start, 
                            split_regex=split_regex, default_return=default_return)
    if not vals:
        return {}
    val_d = {"NA": []}
    prop = "NA"
    for v in vals:
        if v.count(key_value_splitter) == 1:
            prop, v = re.split(key_value_splitter, v)
        if not prop in val_d:
            val_d[prop] = []
        val_d[prop].append(v)
    return val_d

def parse_modifier_vals(d, key_regex, default_start=None, default_return={}, 
                        split_regex=r" *[;,:]+ *", output="dict"): # or "tuples"
    """Parses values of keys that include a modifier (e.g,., AH or CE for dates )

    Example: 
    ```
    >>> d = {
        "30#MS#DATE#AH####:": "02-12-0932",
        "30#MS#DATE#CE####:": "19-09-1526"
    }
    >>> parse_modifier_vals(d, "DATE", default_start="date of")
    >>> parse_modifier_vals(d, "DATE", default_start="date of", output="tuples")
    [("02-12-0932", "AH"), ("19-09-1526", "CE")]
    >>> d = {
        "40#MS#HEIGHT#MM##:": 110,
        "40#MS#HEIGHT#INCH:": 4.33,
    }
    >>> parse_modifier_vals(d, "DATE", default_start="date of")
    {"MM": 110, "INCH": 4.33}
    ```

    Returns: 
       dict
    """
    if output == "dict":
        val_d = dict()
    elif output == "tuples":
        val_list = []
    for k in d:
        if re.findall(key_regex, k):
            val = parse_val_as_str(d, k, default_start=default_start)
            if not val:
                #return default_return
                return copy.deepcopy(default_return)
            
            # get the modifier (AH, CE, MM, CM, ...) from the key:
            #_, _, _, mod = re.split(r"#+", k.strip(":"))
            mod = re.findall("([A-Z]+)#*:", k)[0]
            if output == "dict":
                if mod not in val_d:
                    if split_regex:
                        val_d[mod] = []
                    else:
                        val_d[mod] = ""
            
            if split_regex:
                for v in re.split(split_regex, val):
                    v = v.strip()
                    if output == "dict":
                        if v and v not in val_d[mod]:
                            val_d[mod].append(v)
                    elif output == "tuples":
                        val_list.append((v, mod))
            else:
                if output == "dict":
                    val_d[mod] = val
                elif output == "tuples":
                    val_list.append((val, mod))
    if output == "dict":
        return val_d
    elif output == "tuples":
        return val_list

def parse_language_vals(d, key_component, default_start=None, default_return=({},[],[]), 
                        split_regex=r" *[;,:]+ *", incl_transcr_in_lat_list=False):
    """Parses different language versions of a yml key
    Returns a tuple with three components:
        - dictionary (key: language code, value: list of values)
        - list of arabic-script values
        - list of latin-script values

    Example: 
    ```
    >>> d = {
        "10#LOC#INST#AR###:": "Maktabaŧ Barlīn al-ḥukūmiyyaŧ",
        "10#LOC#INST#DE###:": "Staatsbibliothek zu Berlin",
        "10#LOC#INST#EN###:": "State Library of Berlin",
    }
    >>> r = parse_language_vals(d, "INST", default_start="name of", incl_transcr_in_lat_list=False)
    >>> inst_d, inst_ar, inst_lat = r
    >>> print(inst_d)
    {"AR": "مكتبة برلين الحكومية"}, "DE": "Staatsbibliothek zu Berlin", "EN": "State Library of Berlin"}
    >>> print(inst_lat)
    ["Staatsbibliothek zu Berlin", "State Library of Berlin"]
    >>> r = parse_language_vals(d, "INST", default_start="name of", incl_transcr_in_lat_list=True)
    >>> inst_d, inst_ar, inst_lat = r
    >>> print(inst_lat)
    ["Maktabaŧ Barlīn al-ḥukūmiyyaŧ", "Staatsbibliothek zu Berlin", "State Library of Berlin"]
    ```

    Returns: 
        tuple (dict, list, list)
    """
    val_d = dict()
    ara_script_list = []
    lat_script_list = []
    for k in d:
        if re.findall(key_component, k):
            val = parse_val_as_str(d, k, default_start=default_start)
            if not val:
                return copy.deepcopy(default_return)
            
            # get the language from the key:
            #_, _, _, lang = re.split(r"#+", k.strip(":"))
            lang = re.findall("([A-Z]+)#*:", k)[0]
            if lang not in val_d:
                if split_regex:
                    val_d[lang] = []
                else:
                    val_d[lang] = ""
            
            if split_regex:
                for v in re.split(split_regex, val):
                    v = v.strip()
                    if v and v not in val_d[lang]:
                        if lang in ARABIC_SCRIPT_CODES:
                            ar_v = betacodeToArSimple(v)
                            val_d[lang].append(ar_v)
                            ara_script_list.append(ar_v)
                            if incl_transcr_in_lat_list:
                                lat_script_list.append(v)
                        else:
                            val_d[lang].append(v)
                            lat_script_list.append(v)
            else:
                if lang in ARABIC_SCRIPT_CODES:
                    ar_v = betacodeToArSimple(val)
                    val_d[lang] = ar_v
                    ara_script_list.append(ar_v)
                    if incl_transcr_in_lat_list:
                        lat_script_list.append(val)
                else:
                    val_d[lang].append(val)
                    lat_script_list.append(val)

    return val_d, ara_script_list, lat_script_list
    

def collect_manuscr_yml_data(ms_d, ms_uri=None):
    # - uri
    if not ms_uri:
        ms_uri = ms_d["00#MS#URI########:"]
    
    # - shelfmark
    shelfmark = ms_d["10#MS#SHELFM#####:"]

    # - tags
    tags = parse_val_as_list(ms_d, "10#MS#GENRES####:", default_start="src")
    # tags = []
    # raw_tags = ms_d["10#MS#GENRES#####:"].strip()
    # if raw_tags and not raw_tags.startswith("src"):
    #     for genre in re.split(r" *[,:;]+ *", raw_tags):
    #         if genre.strip():
    #             tags.append(genre.strip())
    tags += ms_d.get("genre_from_text_header", [])

    # - author:
    r = parse_language_vals(ms_d, "AUTHOR", default_start="author(s) on ",
                            incl_transcr_in_lat_list=True)
    author_d, author_ar, author_lat = r
    # author_d = dict()
    # author_ar = []
    # author_lat = []
    # for k in ms_d:
    #     if not "AUTHOR" in k:
    #         continue
    #     if "author(s) on " in ms_d[k] or "none" in ms_d[k].lower():
    #         continue
    #     _, _, _, lang = re.split("#+", k.strip(":"))[-1]
    #     if lang not in author_d:
    #         author_d[lang] = []
    #     if lang in ARABIC_SCRIPT_CODES:
    #         for name in re.split(r" *; *", ms_d[k]):
    #             if not name.strip():
    #                 continue
    #             ar_name = betacodeToArSimple(name.strip())
    #             author_d[lang].append(ar_name)
    #             author_ar.append(ar_name)
    #             author_lat.append(name.strip())
    #     else:
    #         for name in re.split(r" *; *", ms_d[k]):
    #             if not name.strip():
    #                 continue
    #             author_d[lang].append(name.strip())
    #             author_lat.append(name.strip())
    
    # - title:
    r = parse_language_vals(ms_d, "TITLE", default_start="title(s) on ",
                            incl_transcr_in_lat_list=True)
    title_d, title_ar, title_lat = r
    # title_lat = []
    # title_ar = []
    # title_d = dict()
    # for k in ms_d.keys():
    #     if not "TITLE" in k:
    #         continue
    #     v = ms_d[k].strip()
    #     if not v or "title(s) on" in v or "none" in v.lower():
    #         continue
    #     _, _, _, lang = re.split("#+", k.strip(":"))[-1]
    #     if not lang in title_d:
    #         title_d[lang] = []
    #     for title in re.split(r" *; *", v):
    #         title = title.strip()
    #         if title:
    #             if lang in ARABIC_SCRIPT_CODES:
    #                 title_ar.append(betacodeToArSimple(title))
    #                 title_d[lang].append(betacodeToArSimple(title))
    #             else:
    #                 title_d[lang].append(title)
    #             title_lat.append(title)
    
    if "title_from_text_header" in ms_d:
        ttl = ms_d["title_from_text_header"]
        if type(ttl) == str:
            ttl = re.split(r" *[,:;]+ *", ttl)
        for t in ttl:
            t = t.strip()
            if not t:
                continue
            if re.findall("[ء-ي]", t):
                if t not in title_ar:
                    title_ar.append(t)
            else:
                if t not in title_lat:
                    title_lat.append(t)

    normalized_title_lat = [betacodeToSearch(t) for t in title_lat if t]
    
    if title_lat:
        title_lat_prefered = title_lat[0]
    else:
        title_lat_prefered = ""
    if title_ar:
        title_ar_prefered = title_ar[0]
    else: 
        title_ar_prefered = ""

    # - date of writing:
    dates = parse_modifier_vals(ms_d, "DATE", default_start="date of")
    # dates = []
    # for k in ms_d:
    #     if "DATE" in k:
    #         calendar = re.findall(r"([A-Z]+)#*:", k)[0]
    #         raw_dates = ms_d[k].strip()
    #         if raw_dates and not raw_dates.startswith("date of"):
    #             for date in re.split(r" *[:,;]+ *", raw_dates):
    #                 dates.append((date, calendar))

    # - place of writing:
    places = parse_val_as_dict(ms_d, "30#MS#PLACE######:",  default_start="OPIED@ThurayaURI")
    # places = {"NA": []}
    # raw_places = ms_d["30#MS#PLACE######:"].strip()
    # if raw_places and not raw_places.startswith("COPIED@ThurayaURI"):
    #     for place in re.split(r" *[:,;]+ *", raw_places):
    #         place_type = "NA"
    #         if place.count("@") == 1:
    #             place_type, place = re.split(" *@ *", place)
    #             if place_type not in places:
    #                 places[place_type] = []
    #         if place not in places[place_type]:
    #             places[place_type].append(place)

    # - related persons:
    persons = parse_val_as_dict(ms_d, "30#MS#PERSONS####:", default_start="COPYIST@URI")
    # persons = {"NA": []}
    # raw_persons = ms_d["30#MS#PERSONS####:"].strip()
    # if raw_persons and not raw_persons.startswith("COPYIST@URI"):
    #     for person in re.split(r" *[:,;]+ *", raw_persons):
    #         rel_type = "NA"
    #         if person.count("@") == 1:
    #             rel_type, person = re.split(" *@ *", person)
    #             if rel_type not in persons:
    #                 persons[rel_type] = []
    #         if person not in persons[rel_type]:
    #             persons[rel_type].append(person)

    # - institutions mentioned: 
    institutions = parse_val_as_str(ms_d, "30#MS#INSTITUT###:")

    # - script:
    scripts = parse_val_as_dict(ms_d, "30#MS#SCRIPT#####:",
                default_start="Maghribi/Naskh/Nastacliq")
    # scripts = {"NA": []}   # e.g., "ara": "naskh"
    # raw_scripts = ms_d["30#MS#SCRIPT#####:"].strip()
    # if raw_scripts and not raw_scripts.startswith("Maghribi/Naskh/Nastacliq"):
    #     for script in re.split(r" *[:,;]+ *", raw_scripts):
    #         lang_script = "NA"
    #         if script.count("@") == 1:
    #             lang_script, script = re.split(" *@ *", script)
    #             if lang_script not in scripts:
    #                 scripts[lang_script] = []
    #         if script not in scripts[lang_script]:
    #             scripts[lang_script].append(script)

    # - incipit: 
    incipit = parse_val_as_str(ms_d, "40#MS#INCIPIT####:", 
                               default_start="first 5 lines")
    # incipit = ""
    # raw_incipit = ms_d["40#MS#INCIPIT####:"].strip()
    # if raw_incipit and not raw_incipit.startswith("first 5 lines"):
    #     incipit = raw_incipit


    # - explicit:
    explicit = parse_val_as_str(ms_d, "40#MS#EXPLICIT###:", 
                                default_start="last 5 lines")
    # explicit = ""
    # raw_explicit = ms_d[" 40#MS#EXPLICIT###:"].strip()
    # if raw_explicit and not raw_explicit.startswith("last 5 lines"):
    #     explicit = raw_explicit

    # - colophon:
    colophon = parse_val_as_str(ms_d, "40#MS#COLOPHON###:", 
                                default_start="transcription of colophon")
    
    # - dimensions:
    height = parse_modifier_vals(ms_d, "HEIGHT", default_start="height, ")
    width = parse_modifier_vals(ms_d, "WIDTH", default_start="width, ")

    # - ink
    ink = parse_val_as_list(ms_d, "40#MS#INK########:",
                            default_start="color, color")
    
    # - lines per page:
    lines_per_page = parse_val_as_str(ms_d, "40#MS#LINESPP####:",
                                      default_start="lines per page: n")
    
    # - Binding:
    binding = parse_val_as_str(ms_d, "40#MS#BINDING####:",
                                default_start="description of")
    
    # - stamps:
    stamps = parse_val_as_dict(ms_d, "40#MS#STAMPS#####:",
                               default_start="seals and stamps: URI")
    
    # - hands:
    hands = parse_val_as_str(ms_d, "40#MS#HANDS######:",
                                default_start="description of")
    
    # - decoration:
    deco = parse_val_as_str(ms_d, "40#MS#DECO#######:",
                                default_start="description of")
    
    # - columns: 
    columns = parse_val_as_str(ms_d, "40#MS#COLUMNS####:",
                               default_start="number of columns in the manuscript: n")
    
    # - parts:
    parts = parse_val_as_dict(ms_d, "40#MS#PARTS######:",
                              default_start="URI@page_range",
                              split_regex=r" *[;:]+ *")
    
    # - volumes: 
    vols = parse_val_as_str(ms_d, "40#MS#VOLS#######:",
                            default_start="X of Y")
    
    # - external IDs:
    external_ids = get_external_ids(ms_d, "70#MS#EXTID######:")

    # - links
    links = parse_val_as_dict(ms_d, "80#MS#LINKS######:",
                              default_start="SOURCE@permalink")

    # - manuscript catalogue reference:
    catalog_ref = parse_val_as_str(ms_d, "80#MS#CATREF#####:",
                            default_start="reference to a")
    
    # - comments:
    notes = parse_val_as_str(ms_d, "90#MS#COMMENT####:",
                            default_start="a free running comment")
    
    # - tags: 
    tags = parse_val_as_list(ms_d, "90#MS#ISSUES#####:",
                            default_start="comma-separated list")

    ms_meta = dict(
        manuscript_uri=ms_uri,
        shelfmark=shelfmark,
        tags=tags,
        author_d=author_d,
        author_ar=author_ar,
        author_lat=author_lat,
        title_d=title_d, 
        title_ar=title_ar, 
        title_lat=title_lat,
        normalized_title_lat=normalized_title_lat,
        title_lat_prefered=title_lat_prefered,
        title_ar_prefered=title_ar_prefered,
        dates=dates,
        places=places,
        persons=persons,
        institutions=institutions,
        scripts=scripts,
        incipit=incipit,
        explicit=explicit,
        colophon=colophon,
        height=height,
        width=width,
        ink=ink,
        lines_per_page=lines_per_page,
        binding=binding,
        stamps=stamps,
        hands=hands,
        deco=deco,
        columns=columns,
        parts=parts,
        vols=vols,
        external_ids=external_ids,
        links=links,
        catalog_ref=catalog_ref,
        notes=notes,
    )

    return ms_meta

def collect_transcr_yml_data(transcr_d, base_url, corpus_folder=None, 
                             transcr_yml_fp=None, transcr_uri=None, recalculate=False):
    """Collect all metadata from an OpenITI transcription yml file
    
    Args:
        transcr_d (dict): version yml dictionary
        base_url (str): URL on raw.githubusercontents that serves the raw files 
            for the relevant release/current state of the corpus
        corpus_folder (str): path to the (local) folder containing 
            the 25AH year OpenITI corpus folders / RELEASE folder
        version_yml_fp (str): path to the the transcription yml file
        transcr_uri (str): transcription URI
        recalculate (bool): if True, character and token lengths will be recalculated

    Returns:
        version_meta: dict
    """
    # - URI-related variables:
    if not transcr_uri:
        transcr_uri = transcr_d["00#TRNS#URI######:"]
    version_code = transcr_uri.split("-")[0].split(".")[-1]
    languages = re.findall(r"[a-z]{3}", transcr_uri.split("-")[1])
    language = ",".join(languages)
    try:
        #collection_code = re.findall(r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$", version_code)[0]
        collection_code = re.findall(r"^[A-Za-z]+?\d{,2}[A-Za-z]+", version_code)[0]
    except:
        msg = f"no collection code found in '{version_code}'"
        print(msg)
        logger.warning(msg)
        collection_code = None
        #input("CONTINUE?")

    # - most developed text version:

    if "path" in transcr_d:
        pth = transcr_d["path"]
    else:
        pth = transcr_yml_fp[:-4]
    extensions = [".mARkdown", ".completed", ".inProgress", ""]
    for ext in extensions:
        if "extensions" in transcr_d:
            if ext in transcr_d["extensions"]:
                transcr_fp = pth + ext
                break
        else:
            transcr_fp = pth + ext
            if os.path.exists(transcr_fp):
                break
        # if even the path with no extension does not exist:
        if ext == "":
            transcr_fp = ""
            print("NO TEXT VERSION FOUND FOR THIS YML FILE:", transcr_yml_fp)

    # - url:
    if corpus_folder: # data in 25Y folders
        url = transcr_fp.replace(corpus_folder, base_url).replace("\\","/")
        #url = url.replace("AH/data", "AH/master/data")
    else:
        url = base_url.strip("/") + "/" + transcr_fp
        #url = base_url+transcr_fp
        #url = url.replace("/data/", "/master/data/")

    # - annotation status:
    if not ext:
        annotation_status = "(not yet annotated)"
    else:
        annotation_status = ext[1:]

    # - LENGTH:
    char_length = parse_val_as_int(transcr_d, "00#TRNS#CLENGTH##:",
                                   default_start="number of")
    tok_length = parse_val_as_int(transcr_d, "00#TRNS#LENGTH###:",
                                  default_start="number of")
    
    # recalculate the length if it is not present in the yml file:
    if recalculate and not (tok_length and char_length):
        if not char_length:
            char_length = ar_cnt_file(transcr_fp, mode="char")
            transcr_d["00#TRNS#CLENGTH##:"] = str(char_length)
        if not tok_length:
            tok_length = ar_cnt_file(transcr_fp, mode="token")
            transcr_d["00#TRNS#LENGTH###:"] = str(tok_length)

    # - PAGES:
    pages = parse_val_as_str(transcr_d, "40#TRNS#PAGES####:", 
                             default_start="pages transcribed: page_range")
    
    # - EDITION THIS TRANSCRIPTION IS BASED ON:
    based_list = parse_val_as_list(transcr_d, "80#TRNS#BASED####:", 
                                   default_start="permalink,")
    external_ids = {}
    for based_url in based_list:
        org_regex = r"^(?:https?://)?(?:www\.)?(?:[a-z]{2}\.)?(\w+)"
        org = re.findall(org_regex, based_url.strip())
        if org:
            org = org[0]
        else:
            org = "NA"
        if org not in external_ids:
            external_ids[org] = []
        external_ids[org].append(based_url)
    worldcat_links = [v for k, v in external_ids.items() if k.lower() == "worldcat"]
    if "worldcat" in external_ids:
        del external_ids["worldcat"]
    elif "Worldcat" in external_ids:
        del external_ids["Worldcat"]

    links = parse_val_as_str(transcr_d, "80#TRNS#LINKS####:", 
                             default_start="SOURCE@permalink,")
    
    # - OCR MODELS:
    line_model = parse_val_as_str(transcr_d, "80#TRNS#LINMODEL#:", 
                             default_start="segmentation model")
    region_model = parse_val_as_str(transcr_d, "80#TRNS#REGMODEL#:", 
                             default_start="segmentation model")
    recognition_model = parse_val_as_str(transcr_d, "80#TRNS#RECMODEL#:", 
                             default_start=None)
    
    # - CONTRIBUTORS:
    contributors = parse_val_as_dict(transcr_d, "90#TRNS#CONTRIB##:",
                                     default_start="TRANSCRIPTION@name")    
    # - COMMENTS:
    notes = parse_val_as_str(transcr_d, "90#TRNS#COMMENT##:",
                             default_start="a free running comment")
    
    # - ISSUES:
    issues = parse_val_as_str(transcr_d, "90#TRNS#ISSUES###:",
                              default_start="comma-separated list")
    issues = re.findall(r"[A-Z_]{5,}", issues)

    uncorrected_OCR = False
    if "UNCORRECTED_OCR" in issues:
        uncorrected_OCR=True

    primary_yml = ""
    if "PRIMARY_VERSION" in issues:
        primary_yml = "pri"
    else:
        primary_yml = "sec"

    transcr_meta = dict(
        # version_meta:
        version_uri=transcr_uri,
        version_code=version_code,
        language=language,
        collection_code=collection_code,
        text_meta="",
        edition_meta="",
        # release_version_meta:
        char_length=char_length,
        tok_length=tok_length, 
        path=transcr_fp,
        url=url,
        pages=pages,                # not in version_record yet
        analysis_priority=primary_yml,
        annotation_status=annotation_status,
        notes=notes,
        tags=" :: ".join(issues),
        header_meta=transcr_d.get("header_meta", {}),
        line_model=line_model,      # not in version_record
        region_model=region_model,  # not in version_record
        recognition_model=recognition_model,  # not in version_record
        contributors=contributors,  # not in version_record
        subcorpus="MSS",
        uncorrected_OCR=uncorrected_OCR,
        # edition_meta:
        external_ids=external_ids,  
        worldcat_links=worldcat_links,  # not in version_record yet
        pdf_url=links,
    )
    return transcr_meta

def collect_author_yml_data(auth_d, author_uri=None):
    """Collect all metadata from an OpenITI author yml file"""

    if not author_uri:
        author_uri = auth_d["00#AUTH#URI######:"]

    # collect death and birth dates from yml keys:
    birth_dates = parse_modifier_vals(auth_d, "30#AUTH#BORN", default_start="YEAR-MON-DA")
    death_dates = parse_modifier_vals(auth_d, "30#AUTH#DIED", default_start="YEAR-MON-DA")
    dates = {"birth": birth_dates, "death": death_dates}

    # collect the author's dates from the URI:
    date_str = author_uri[:4]
    date = int(date_str)
    date_AH = date
    #date_CE = ah2ce(date)

    # process the name elements:
    name_d = {"LAT": {}}
    for k in auth_d:
        if re.findall("^10#.+(?:LAQAB|KUNYA|ISM|NASAB|NISBA|SHUHRA)", k):
            if "Fulān" in auth_d[k] or "none" in auth_d[k].lower():
                continue
            try:
                _, _, name_el, lang = re.split("#+", k.strip(":"))
            except Exception as e:
                msg = f"{e}: failed to parse name element key '{k}' in {author_uri}"
                logger.warning(msg)
                print(msg)
                # print(e)
                # print(k)
                # print(k.strip(":"))
                # print(re.split("#+", k.strip(":")))
                #input("CONTINUE?")
            if lang not in name_d:
                name_d[lang] = {}
            if lang in ARABIC_SCRIPT_CODES:
                name_d[lang][name_el.lower()] = betacodeToArSimple(auth_d[k])
                name_d["LAT"][name_el.lower()] = auth_d[k]
            else:
                name_d[lang][name_el.lower()] = auth_d[k]
    
    # create a full name from the name elements:
    name_comps = "LAQAB|KUNYA|ISM|NASAB|NISBA".lower().split("|")
    for lang in name_d:
        d = name_d[lang]
        full_name = [d[k] for k in name_comps if k in d and d[k].strip()]
        full_name = " ".join(full_name)
        if lang in ARABIC_SCRIPT_CODES:
            name_d[lang]["full_name"] = betacodeToArSimple(full_name)
        else:
            name_d[lang]["full_name"] = full_name

    # create the legacy shuhra variables:
    shuhra = ""
    shuhra_ar = ""
    shuhras = {}
    for lang in name_d:
        for k,v in name_d[lang].items():
            if "shuhra" in k:
                shuhras[lang] = v
    if shuhras: 
        for lang in ["LAT", "EN", "FR", "DE"]:
            if lang in shuhras:
                shuhra = shuhras[lang]
                break
        for lang in ARABIC_SCRIPT_CODES:
            if lang in shuhras:
                shuhra_ar = shuhras[lang]
                break
    
    # create the legacy full_name variables:
    full_name = ""
    full_name_ar = ""
    full_names = {}
    for lang in name_d:
        for k,v in name_d[lang].items():
            if "full_name" in k:
                full_names[lang] = v
    if full_names: 
        for lang in ["LAT", "EN", "FR", "DE"]:
            if lang in full_names and full_names[lang]:
                full_name = full_names[lang]
                break
        for lang in ARABIC_SCRIPT_CODES:
            if lang in full_names and full_names[lang]:
                full_name_ar = full_names[lang]
                break
    if not shuhra:
        shuhra = full_name
    if not shuhra_ar:
        shuhra_ar = full_name_ar
    
    english_name = ""
    if "EN" in name_d:
        if "SHUHRA" in name_d["EN"]:
            english_name = name_d["EN"]["shuhra"]
        elif "full_name" in name_d["EN"]:
            english_name = name_d["EN"]["full_name"]
    
    name_from_uri = author_uri[4:]
    name_from_uri = insert_spaces(name_from_uri)
    name_from_uri = replace_c_with_cayn(name_from_uri)

    # print(name_d)
    # print("shuhra:", shuhra)
    # print("shuhra_ar:", shuhra_ar)
    # print("full_name_ar:", full_name_ar)
    # print("full_name:", full_name)
    # print("full_names:", full_names)
    # print("============")

    # create more legacy name values:
    author_ar = []
    author_lat = []
    for lang in ["LAT", "EN", "FR", "DE"]:
        if lang in shuhras:
            author_lat.append(shuhras[lang])
        if lang in full_names:
            author_lat.append(full_names[lang])
        if english_name:
            author_lat.append(english_name)
        author_lat.append(name_from_uri)
    for lang in ARABIC_SCRIPT_CODES:
        if lang in shuhras:
            author_ar.append(shuhras[lang])
        if lang in full_names:
            author_ar.append(full_names[lang])
    normalized_author_lat = [betacodeToSearch(a) for a in author_lat]
    author_ar_prefered = shuhra_ar or full_name_ar
    author_lat_prefered = shuhra or full_name or english_name or name_from_uri

    # add data from header:
    if not author_ar and "name_from_text_header" in auth_d:
        header_names = auth_d["name_from_text_header"]
        if type(header_names) == str:
            header_names = re.split(r" *[:;,]+ *", header_names)
        for n in header_names:
            n = n.strip()
            if not n:
                continue
            if re.findall("[ء-ي]", n):
                if n not in author_ar:
                    author_ar.append(n)
                    if not author_ar_prefered:
                        author_ar_prefered = n
            else:
                if n not in author_lat:
                    author_lat.append(n)
                    if not author_lat_prefered:
                        author_lat_prefered = n

    # print(name_d)
    # print("shuhra:", shuhra)
    # print("shuhra_ar:", shuhra_ar)
    # print("full_name_ar:", full_name_ar)
    # print("full_name:", full_name)
    # print("full_names:", full_names)
    # print("author_lat_prefered:", author_lat_prefered)
    # print("author_ar_prefered:", author_ar_prefered)
    # #input()

    # geo data:
    geo_regex = r"\w+_RE(?:_\w+)?|\w+_[RSNO]\b|\w+XXXYYY\w*"
    place_relations = []
    
    born = re.findall(geo_regex, auth_d.get("20#AUTH#BORN#####:", ""))
    for p in born:
        place_relations.append(dict(
            code="BORN", 
            subtype_code="", 
            person_a=author_uri, 
            place_b=p
        ))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
        
    died = re.findall(geo_regex, auth_d.get("20#AUTH#DIED#####:", ""))
    for p in died:
        place_relations.append(dict(
            code="DIED", 
            subtype_code="", 
            person_a=author_uri, 
            place_b=p
        ))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
    
    resided = re.findall(geo_regex, auth_d.get("20#AUTH#RESIDED##:", ""))
    for p in resided:
        place_relations.append(dict(
            code="RESID", 
            subtype_code="", 
            person_a=author_uri, 
            place_b=p
        ))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)
    
    visited = re.findall(geo_regex, auth_d.get("20#AUTH#VISITED##:", ""))
    for p in visited:
        place_relations.append(dict(
            code="VISIT", 
            subtype_code="", 
            person_a=author_uri, 
            place_b=p
        ))
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(author_uri)

    # person_relations:
    person_relations = []
    if "40#AUTH#STUDENTS#:" in auth_d:
        if not "from OpenITI" in auth_d["40#AUTH#STUDENTS#:"]:
            for student in auth_d["40#AUTH#STUDENTS#:"].split(","):
                student_uri = re.findall(r"\d{4}[A-Z][a-zA-Z]+", student)
                if student_uri:
                    if not student.strip() == student_uri[0]:
                        print("Additional information in student field?", student)
                    person_relations.append(dict(
                        code="STUDENT", 
                        subtype_code="", 
                        person_a=student_uri[0], 
                        person_b=author_uri
                    ))
    else:
        print("MISSING KEY 40#AUTH#STUDENTS# in", author_uri)
        print(json.dumps(auth_d, indent=2, ensure_ascii=False))
        #input()
    if not "from OpenITI" in auth_d["40#AUTH#TEACHERS#:"]:
        for teacher in auth_d["40#AUTH#TEACHERS#:"].split(","):
            teacher_uri = re.findall(r"\d{4}[A-Z][a-zA-Z]+", teacher)
            if teacher_uri:
                if not re.sub(r"[\s¶]+", "", teacher) == teacher_uri[0]:
                    print("Additional information in teacher field?", teacher)
                person_relations.append(dict(
                    code="STUDENT", 
                    subtype_code="", 
                    person_a=author_uri, 
                    person_b=teacher_uri[0]
                ))

    # collect external IDs:
    external_ids = get_external_ids(auth_d, "70#AUTH#EXTID####:")
    # external_ids = dict()
    # if "70#AUTH#EXTID####:" in auth_d:
    #     ext_ids = auth_d["70#AUTH#EXTID####:"].strip().lower()
    #     if ext_ids not in ["", "none", "viaf@id, wikidata@id, src@id"]:
    #         for ext_id in re.split(r" *[;,:]+ *", ext_ids):
    #             try:
    #                 src, id_ = ext_id.split("@")
    #             except:
    #                 src = "NA"
    #                 id_ = ext_id
    #             if src not in external_ids:
    #                 external_ids[src] = []
    #             external_ids[src].append(id_)                

    # collect bibliography:
    bibliography = ""
    raw_bib = auth_d["80#AUTH#BIBLIO###:"].strip()
    if raw_bib and not raw_bib.startswith("src@id"):
        bibliography = re.sub(r"\s+", " ", raw_bib)

    # collect notes:
    notes = ""
    if "90#AUTH#COMMENT##:" in auth_d:
        raw_notes = auth_d["90#AUTH#COMMENT##:"].strip()
        if raw_notes and not raw_notes.startswith("a free running comment"):
            notes = re.sub(r"\s+", " ", raw_notes)
    else:
        print("MISSING KEY: 90#AUTH#COMMENT##: in", author_uri)
        print(json.dumps(auth_d, indent=2, ensure_ascii=False))
        #input()

    author_meta = dict(
        author_uri=author_uri,
        date=date,
        date_AH=date_AH,
        #date_CE=date_CE,
        dates=dates,
        date_str=date_str,
        author_ar=" :: ".join(author_ar),
        author_lat=" :: ".join(list(set(author_lat + normalized_author_lat))),
        author_ar_prefered=author_ar_prefered,
        author_lat_prefered=author_lat_prefered,
        author_from_uri=name_from_uri,
        name_elements=name_d,
        place_relations=place_relations,
        person_relations=person_relations,
        external_ids=external_ids,
        bibliography=bibliography,
        notes=notes,
        tags="",
        )
    return author_meta

def get_external_ids(d, ext_id_key,
                     defaults=["", "none", "viaf@id, wikidata@id, src@id"]):
    """Get a dictionary of external IDs from a yml dictionary.
    
    Keys in the dictionary are external ID providers;
    values are all external IDs from this provider
    
    Args:
        d (dict): a yml dictionary
        ext_id_key (str): the key that contains the external IDs
            in that yml dictionary
    """
    # check if the key exists and is not empty or default:
    if ext_id_key not in d:
        return {}
    ext_id_str = d[ext_id_key].strip().lower()
    if ext_id_str in defaults:
        return {}
    
    external_ids = {}
    for ext_id in re.split(r" *[;,:]+ *", ext_id_str):
        try:
            src, id_ = ext_id.split("@")
        except:
            src = "NA"
            id_ = ext_id
        if src not in external_ids:
            external_ids[src] = []
        external_ids[src].append(id_)
    return external_ids

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
        

def get_github_issues(token_fp="api/util/GitHub personalAccessTokenReadOnly.txt"):
    """Get annotation issues from GitHub"""
    try:
        with open(token_fp, mode="r", encoding="utf-8") as file:
            github_token = file.read().strip()
    except:
        github_token = None # you will be prompted to insert the token manually

    issues = get_issues.get_issues("OpenITI/Annotation",
                                   access_token=github_token,
                                   issue_labels=["URI change suggestion",
                                                 "text quality",
                                                 "PRI & SEC Versions"])
    issues = get_issues.define_text_uris(issues)
    issues_uri_dict = get_issues.sort_issues_by_uri(issues)
    return issues_uri_dict
