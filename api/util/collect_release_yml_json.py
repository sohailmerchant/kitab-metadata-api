"""
Create a json file that contains all the yml files in a release.

This version of the script makes sure the files
from the 9001AH and PER9001AH repos are included.

To generate the json file for a specific release,
first check out that release,
in the RELEASE, 9001AH and PER9001AH repos:

```
git checkout v2023.1.8
```

And provide the paths to those folders at the bottom of this script.

Two options for the output:

- dictionary structure:

{author_uri}:
  "meta": {**author_yml_d, "path"}
  {book_uri}:
     "meta": {**book_yml_d, "path"}
     {version_uri}: {**version_yml_d, "path", "extensions"}

- list structure:

[
  {
    **author_yml,
    "name_from_text_header",
    "date_from_text_header",
    "path",
    "books": [
      {
        **book_yml,
        "path",
        "title_from_text_header",
        "genre_from_text_header",
        "versions": [
          {
            **version_yml,
            "path",
            "extensions",
            "header_meta"
            
          }
        ]
   ]
  }
]
"""

import json
import os
import re
import sys


from openiti.helper.yml import ymlToDic
from openiti.helper.templates import author_yml_template, book_yml_template, \
     version_yml_template, location_yml_template, manuscript_yml_template, \
     transcription_yml_template

# group the metadata keys in the text file headers
# into categories:
headings_dict = {  
     'Iso' : "Title", 
     'Lng' : "AuthorName",
     'lng' : "AuthorName",
     'higrid': "Date",
     'HigriD': "Date",
     'auth' : "AuthorName",
     '001.AuthorNAME': "AuthorName",
     '002.AuthorSHORTNAME': "AuthorName",
     '011.AuthorBORN': 'BirthDate',
     '004.AuthorBORN': "BirthDate",
     'auth.x' : "AuthorName",
     'auth.y': "AuthorName",
     'bk' : "Title", # 
     'cat' : "Genre", # Values: max 3-digit integer
     'name' : "Genre", 
     'البلد' : "Edition:Place", 
     'الطبعة' : "Edition:Date", # date + number (al-ula, al-thaniya, ...)
     'الكتاب' : "Title", 
     'المؤلف' : "AuthorName",
     'تصنيف': "AuthorName",
     'المحقق' : "Edition:Editor",
     'جمع وترتيب': "Edition:Editor",
     'الناشر' : "Edition:Publisher", 
     'تأليف' : "AuthorName", 
     'تحقيق' : "Edition:Editor", 
     'تقديم وتعليق' : "Edition:Editor",
     'تقديم' : "Edition:Editor", 
     'حققه' : "Edition:Editor", 
     'خرج أحاديثه' : "Edition:Editor", 
     'دار النشر' : "Edition:Publisher", 
     'دراسة وتحقيق' : "Edition:Editor", 
     'سنة الطبع' : "Edition:Date", 
     'سنة النشر' : "Edition:Date",
     'تاریخ الطبعة': "Edition:Date",
     'شهرته' : "AuthorName", 
     'عام النشر' : "Edition:Date",
     'تاريخ النشر': "Edition:Date",
     'مكان النشر' : "Edition:Place", 
     'وضع حواشيه' : "Edition:Editor", 
     'أشرف عليه وراجعه وقدم له' : "Edition:Editor", # thesis supervisor
     'حققه وقدم له وعلق عليه': "Edition:Editor",
     'حققه وقدم له': "Edition:Editor",
     
     'أصدرها':  "Edition:Editor",
     'أعتنى به' : "Edition:Editor",
     'أعد أصله' : "Edition:Editor",
     'أعده' : "Edition:Editor",
     'أعده للنشر' : "Edition:Editor",
     'أعده ونشره' : "Edition:Editor",
     'ألحقها' : "Edition:Editor",
     'تقديم وإشراف ومراجعة' : "Edition:Editor",
     'المواضيع': "Genre",
     '010.AuthorAKA' : "AuthorName", 
     '010.AuthorNAME' : "AuthorName",
     '001.AuthorNAME' : "AuthorName",
     '011.AuthorDIED' : "Date", 
     '019.AuthorDIED' : "Date",
     '006.AuthorDIED' : "Date",
     '020.BookAUTHOR' : "AuthorName",
     '020.BookTITLE' : "Title",
     '010.BookTITLE' : "Title",
     '021.BookSUBJ' : "Genre", # separated by :: 
     '029.BookTITLEalt' : "Title",
     '011.BookSHORTTITLE': "Title",
     '040.EdEDITOR' : "Edition:Editor", 
     '043.EdPUBLISHER' : "Edition:Publisher",
     '013.EdPUBLISHER' : "Edition:Publisher",
     '044.EdPLACE' : "Edition:Place", 
     '045.EdYEAR' : "Edition:Date",
     '015.BookGENRE' : "Genre",
     'classification': "Genre",
     'documentType': "Genre",
     'title' : "Title",
     'title_ar': "Title",
     'نام كتاب': "Title",
     'اسم الكتاب': "Title",
     'سنة الوفاة': "Date",
     'تاريخ وفاة المؤلف': "Date",
     'نويسنده': "AuthorName",
     'ناشر' : "Edition:Publisher",
     'المطبعة': "Edition:Publisher",
     'تاريخ نشر' : "Edition:Date",
     'مكان چاپ' : "Edition:Place",
     'مكان الطبع': "Edition:Place",
     'محقق/ مصحح' : "Edition:Editor",
     'مصحح' : "Edition:Editor",
     'محقق' : "Edition:Editor",
     'تحقيق ودراسة': "Edition:Editor",
     'تحقيق وتعليق': "Edition:Editor",
     'حققه وعلق عليه': "Edition:Editor",
     'دراسة وتحقيق وتعليق': "Edition:Editor",
     'راجعه وصححه وعلق عليه': "Edition:Editor",
     'تقديم وتعليق': "Edition:Editor",
     'تقديم وتحقيق': "Edition:Editor",
     'حرره وضبطه': "Edition:Editor",
     'تاريخ نشر' : "Edition:Date",
     'تاريخ وفات مؤلف' : "Date",
     'موضوع' : "Genre",
     'المتوفى': "Date",
     'المتوفي': "Date",
     'سنة الولادة': "BirthDate",
     'العنوان': "Title",
     'عنوان الكتاب': "Title",
     'Title' : "Title",
     'title' : "Title",
     'Translator': "Translator",
     'المترجم': "Translator",
     'تعريب': "Translator",
     'Editor': "Edition:Editor",
     'principalEditor': "Edition:Editor",
     'Publisher': "Edition:Publisher",
     'Place of Publication': "Edition:Place",
     'Date of Publication': "Edition:Date",
     'Author': "AuthorName",
     'author': "AuthorName",
     'source': "Edition:Place",  # in PAL texts: manuscript data
     'Date of Pulbication': "Edition:Date",
     'Date': "Date",
     'نسخ': "Copyist",
     'اعتنى به': "Edition:Editor",
     'تخريج': "Edition:Editor",
     'title_transcription': "TitleLat",
     'title_latin': "TitleLat",
     'title_short': "Title",
     'author_latin': "TitleLat",
     'Title (EN)': "TitleLat",
     'title_en': "TitleLat",
     'author_transcription': "AuthorNameLat",
     'Genres': "Genre",
     }

# Create a list of default values for each yml key
# (this helps checking whether or not to overwrite a value)
default_values = dict()
templates = [author_yml_template, book_yml_template,
     version_yml_template, location_yml_template,
     manuscript_yml_template, transcription_yml_template]
for template in templates:
    default_values.update(ymlToDic(template))

# keep track of the number of different metadata header keys:
key_counter = dict()


def sort_extensions(ext_list, importance=[".mARkdown", ".completed", ".inProgress", ""]):
    """sort extensions in order of importance

    Args:
        ext_list (list): list of extensions to be ordered
        importance (list): list of extensions in order of importance.
            extensions in ext_list but not in importance
            will be appended at the end of the list of sorted extensions

    Returns:
        List
    
    """
    sorted_ext = [ext for ext in importance if ext in ext_list]
    other_ext = [ext for ext in ext_list if ext not in importance]
    return sorted_ext + other_ext
    

def list_extensions(book_folder, version_uri, importance=[".mARkdown", ".completed", ".inProgress", ""]):
    """Create a list of all extensions of a text version;
    and sort them by decreasing importance.

    Args:
        book_folder (str): path to the book folder that contains the versions
        version_uri (str): OpenITI version URI
        importance (list): list of extensions, sorted by decreasing importance

    Returns:
        list
    """
    extensions = []
    for fn in os.listdir(book_folder):
        if version_uri in fn and not fn.endswith(".yml"):
            extensions.append(fn[len(version_uri):]) # inludes period!
    
    return sort_extensions(extensions, importance)   

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

def clean_val(val):
    """Clean a yml value."""
    val = re.sub(r"[\s¶]+", " ", val)
    return val

def parse_header_item(key, value, all_meta, meta, coll_id, shamela_bitaqa=False):
    """Parse a line in an OpenITI text file header,
    and add it to the metadata dictionary for this text version.

    Args:
        key (str): key of the metadata item
        value (str): value of the metadata item
        all_meta (dict): dictionary containing all metadata
            related to the current text version,
            with the original keys
        meta (dict): dictionary containing all metadata
            related to the current text version,
            with normalized keys (categories)
        coll_id (str): collection ID
        shamela_bitaqa (bool): set to True if the previous line
            indicates that this line is a rendition of the
            short metadata dictionary that is called Betaqa
            in al-Maktaba al-Shamela

    Returns:
        None
    """
    for val in re.split(r" :: ", value):
        val = val.strip()
        if val.upper().startswith("NO"):
            continue
        if val == "":
            continue

        if val.isnumeric():
            val = str(int(val))
        
        key = re.sub(r"\# ", "", key)
        all_meta[key] = val

##        # check if there are other categories on the same line:
##        # UPDATE: THIS IS OFTEN SHAMELA BITAQA, which is already parsed further in the header        
##        if not shamela_bitaqa and re.findall(r"¶ *\w+ *:", val):
##            print("SPLIT:")
##            print("-", key)
##            print("-", val)
##            val, key2, val2 = re.split(r"¶ *(\w+) *: *", val, maxsplit=1)
##            parse_header_item(key2, val2, all_meta, meta, coll_id)
##        if shamela_bitaqa:
##            print("SHAMELA_BITAQA:", val)
        
        # reorganize the relevant headers under overarching categories:
        if key in headings_dict:
            cat = headings_dict[key]
            if cat == "Genre" and coll_id and val:
                val = f"{coll_id}@{val}"

            meta[cat].append(clean_val(val))
        else:
            if key not in meta:
                meta[key] = []
            meta[key].append(clean_val(val))
    key_counter[key] = key_counter.get(key, 0) + 1

def extract_metadata_from_header(fp, coll_id, VERBOSE=False):
    """Extract the metadata from the metadata header of a text file.

    Args:
        fp (str): path to the text file
        coll_id (str): collection ID
        VERBOSE (bool): if True, debugging data will be printed

    Returns:
        meta (dict): dictionary containing relevant extracted header items
    """
    header = read_header(fp)
    categories = "AuthorName AuthorNameLat Translator Copyist Title TitleLat Date BirthDate Genre "
    categories += "Edition:Editor Edition:Publisher Edition:Place Edition:Date"
    meta = {x : [] for x in categories.split()}
    unreadable = []
    all_meta = dict()
    shamela_bitaqa = False
    
    for line in header:
##        split_line = line[7:].split("\t::")  # [7:] : start reading after #META# tag
##        if len(split_line) == 1:
##            split_line = line[7:].split(": ", 1)  # split after first colon
        split_line = re.split(r"[\t ]*:+[\t ]*", line[7:], maxsplit=1)
        if len(split_line) == 2:
            key, value = split_line
            if "Shamela_short_metadata_record" in key:
                #print("BITAQA!")
                shamela_bitaqa = True
                if value.strip() == "":
                    #print("-> skipping")
                    continue  #
                else:
                    value = f"{key}: {value}"
            if shamela_bitaqa:
                key = "Shamela_short_metadata_record"

            parse_header_item(key, value, all_meta, meta, coll_id,
                                  shamela_bitaqa=shamela_bitaqa)
            shamela_bitaqa = False
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

def update_dict(d1, d2):
    """update a dictionary with the values from another dictionary,
    checking for default values."""
    for k,v in d2.items():
        if k not in d1:
            d1[k] = v
        elif d1[k] == v:
            continue
        else:
            if k in default_values:
                # if the new value is default value,
                # don't replace the existing value with the new value:
                if v.startswith(default_values[k][:10]):
                    continue
                # if the old value is default,
                # replace it with the new, non-default value:
                elif d1[k].startswith(default_values[k][:10]):
                    d1[k] = v
##            elif k == "extensions":
##                d1[k] = sort_extensions(list(set(d1[k]+v)))
            else:
                print("KEY:", k)
                print("Original value:", d1[k])
                print("New value:", v)
                r = input("Replace value? Y/n (or write the new value):\n")
                if r.upper().strip() == "Y":
                    d1[k] = v
                elif r.upper().strip() == "":
                    d1[k] = v
                elif r.upper().strip() != "N":
                    d1[k] = r
            
    return d1
            
            

def collect_yml_meta(start_folder, release_no, outfolder="../../meta", verbose=True,
                     json_format="dict", json_d=dict()):
    
    not_found = []
    for author in os.listdir(start_folder):
        if verbose:
            print(author)
        author_folder = os.path.join(start_folder, author)
        if not os.path.isdir(author_folder):
            continue
        if author not in json_d:
            json_d[author] = {}
        
        for book in os.listdir(author_folder):
            fp = os.path.join(author_folder, book)
            if fp.endswith(".yml"):  # AUTHOR/LOC YML
                with open(fp, mode="r", encoding="utf-8") as file:
                    d = ymlToDic(file.read().replace("¶    ", " "))
                    d["path"] = author
                    if "meta" not in json_d[author]:
                        json_d[author]["meta"] = {}
                    #json_d[author]["meta"].update(d)
                    update_dict(json_d[author]["meta"], d)
            if not os.path.isdir(fp):
                continue
            book_folder = fp
            for fn in os.listdir(book_folder):
                if fn.endswith(".yml"):
                    fp = os.path.join(book_folder, fn)
                    with open(fp, mode="r", encoding="utf-8") as file:
                        d = ymlToDic(file.read().replace("¶    ", " "))
                    if fn.count(".") == 2:  # BOOK / MANUSCRIPT YML
                        d["path"] = f"{author}/{book}"
                        if book not in json_d[author]:
                            json_d[author][book] = {"meta": dict()}
                        update_dict(json_d[author][book]["meta"], d)
##                            json_d[author][book] = {"meta": d}
##                        else:
##                            json_d[author][book]["meta"].update(d)
                            
                        
                    elif fn.count(".") == 3: # VERSION/TRANSCRIPTION YML
                        version_uri = fn[:-4]
                        version_code = version_uri.split("-")[0].split(".")[-1]
                        try:
                            #coll_regex = r"^([A-Za-z]+?\d*[A-Za-z]+)\d+(?:BK\d+)?(?:Vols)?[A-Z]?$"
                            coll_regex = r"^[A-Za-z]+?\d{,2}[A-Za-z]+"
                            collection_code = re.findall(coll_regex, version_code)[0]
                            
                        except:
                            collection_code= ""

                        extensions = list_extensions(book_folder, version_uri)
                        d["extensions"] = extensions
                        d["path"] = f"{author}/{book}/{version_uri}"
                        d["header_meta"] = dict()
                        
                        fp = os.path.join(start_folder, d["path"])
                        if extensions:
                            fp += extensions[0]
                        if not os.path.exists(fp):
                            print("TEXT FILE NOT FOUND!!", fp)
                            not_found.append(fp)
                            continue
                        header_meta_d = extract_metadata_from_header(fp, collection_code)
                        for k,v in header_meta_d.items():
                            if k not in d["header_meta"]:
                                d["header_meta"][k] = []
                            for el in v:
                                if el not in d["header_meta"][k]:
                                    d["header_meta"][k].append(el)
                        
                        # add the author-related header metadata to the author meta key:
                        if author not in json_d:
                            json_d[author] = {"meta": {}}
                        if "meta" not in json_d[author]:
                            json_d[author]["meta"] = {}
                        if "name_from_text_header" not in json_d[author]["meta"]:
                            json_d[author]["meta"]["name_from_text_header"] = []
                            json_d[author]["meta"]["date_from_text_header"] = []
                        #json_d[author]["meta"]["name_from_text_header"] += header_meta_d["AuthorName"]
                        #json_d[author]["meta"]["date_from_text_header"] += header_meta_d["Date"]
                        for name in header_meta_d["AuthorName"]:
                            name = name.strip()
                            if name and name not in json_d[author]["meta"]["name_from_text_header"]:
                                json_d[author]["meta"]["name_from_text_header"].append(name)
                        for date in header_meta_d["Date"]:
                            data = date.strip()
                            if date and date not in json_d[author]["meta"]["date_from_text_header"]:
                                json_d[author]["meta"]["date_from_text_header"].append(date)
                                
                        # add the book-related header metadata to the book meta key:
                        if book not in json_d[author]:
                            json_d[author][book] = {"meta": {}}
                        if "meta" not in json_d[author][book]:
                            json_d[author][book]["meta"] = {}
                        if "title_from_text_header" not in json_d[author][book]["meta"]:
                            json_d[author][book]["meta"]["title_from_text_header"] = []
                            json_d[author][book]["meta"]["genre_from_text_header"] = []

                        for t in header_meta_d["Title"]:
                            t = t.strip()
                            if t and t not in json_d[author][book]["meta"]["title_from_text_header"]:
                                json_d[author][book]["meta"]["title_from_text_header"].append(t)
                        #json_d[author][book]["meta"]["title_from_text_header"] += header_meta_d["Title"]
                        for g in header_meta_d["Genre"]:
                            g = g.strip()
                            if not g:
                                continue
                            if collection_code and "@" not in g:
                                g = f"{collection_code}@{g}"
                            if g not in json_d[author][book]["meta"]["genre_from_text_header"]:
                                json_d[author][book]["meta"]["genre_from_text_header"].append(g)
                            
                        if book in json_d[author]:
                            json_d[author][book][version_uri] = d
                        else:
                            json_d[author][book] = {version_uri: d}
                        
                        
                        
                        
    outfn = f"all_ymls_in_release-{release_no.replace('.', '_')}_{json_format}.json"
    outfp = os.path.join(outfolder, outfn)
    with open(outfp, mode="w", encoding="utf-8") as file:
        json.dump(json_d, file, indent=2, ensure_ascii=False)
    if json_format == "list":
        json_list = convert_to_list(json_d)
        with open(outfp, mode="w", encoding="utf-8") as file:
            json.dump(json_list, file, indent=2, ensure_ascii=False)

    if not_found:
        print("WARNING:", len(not_found), "text files not found!")
        for fp in not_found:
            print(fp)
    
    print("JSON file can be found here:", outfp)

    return json_d

def convert_to_list(json_d):
    json_list = []
    for author in json_d:
        if author == "9001AH":
            continue
        if author.startswith("MS"):
            loc = author
            loc_meta = json_d[loc]["meta"]
            loc_meta["manuscripts"] = []
            json_list.append(loc_meta)
            for mk in json_d[loc]:
                if mk == "meta":
                    continue
                manuscript_meta = json_d[loc][mk]["meta"]
                manuscript_meta["transcriptions"] = []
                loc_meta["manuscripts"].append(manuscript_meta)
                for vk in json_d[loc][mk]:
                    if vk == "meta":
                        continue
                    manuscript_meta["transcriptions"].append(json_d[loc][mk][vk])
        else:
            author_meta = json_d[author]["meta"]
            author_meta["books"] = []
            json_list.append(author_meta)
            for bk in json_d[author]:
                if bk == "meta":
                    continue
                book_meta = json_d[author][bk]["meta"]
                book_meta["versions"] = []
                author_meta["books"].append(book_meta)
                for vk in json_d[author][bk]:
                    if vk == "meta":
                        continue
                    book_meta["versions"].append(json_d[author][bk][vk])

    return json_list

if __name__ == "__main__":
    print("Are you sure you have checked out the correct tag of the RELEASE and 9001AH folders?")
    r = input("press 'Y' and Enter to continue: ")
    if r.strip().upper() != "Y":
        print("Aborting")
        sys.exit(0)
    
    release_no = input("Please provide the release number (e.g., 2021.2.5): ")

    outfolder = input("Please provide the path to the folder where the output should be stored: ")
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)


    start_folder = input("Please provide the path to the data folder inside the release folder: ")
    if not re.findall(r"data/?$", start_folder):
        start_folder = input("Path does not end with '/data'. Please provide the path to the data folder inside the release folder: ")
    json_d = collect_yml_meta(start_folder.rstrip("/"), release_no, outfolder=outfolder, json_format="list")

    r = "CONTINUE"
    while r:
        print("Do you want to add metadata from another, private folder (e.g., 9001AH)?")
        r = input("Please provide the path to the data folder inside that private folder (or press Enter to stop): ")
        if not r.strip(): 
            break
        if not re.findall(r"data/?$", r):
            r = input("Path does not end with '/data'. Please provide the path to the data folder inside the private folder: ")
        json_d = collect_yml_meta(r.rstrip("/"), release_no, outfolder=outfolder, json_format="list", json_d=json_d)