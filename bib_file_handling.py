import bibtexparser
from bibtexparser.bparser import BibTexParser
import pandas as pd
import re
from bibtexparser.bwriter import BibTexWriter
from rapidfuzz.fuzz import token_set_ratio
from rapidfuzz.fuzz import partial_ratio
from rapidfuzz import fuzz
from quantitative_analysis import QA_algo

def abbreviate_author_names(filename):
    # Load .bib file
    with open(filename, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser(common_strings=True)
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Process each entry to abbreviate only the first author
    for entry in bib_database.entries:
        if 'author' not in entry:
            continue

        authors = entry['author'].split(' and ')
        first_author = authors[0]

        # Remove digits and normalize hyphens
        first_author = re.sub(r'\d+', '', first_author).strip()
        first_author = first_author.replace("-", " ")
        name_parts = first_author.split()
        if '.' in name_parts[-1]: continue #'.' is in last part of name --> abbreviated already
        if len(name_parts) < 2:
            formatted_author = first_author
        else:
            lastname = name_parts[-1]
            initials = ''
            for part in name_parts[:-1]:
                if len(part) == 2 and part[1] == '.':
                    initials += part  # Already abbreviated like "G."
                else:
                    initials += part[0].upper() + '.'
            formatted_author = f"{lastname} {initials}"

        # Replace entire author field with formatted first author only
        entry['author'] = formatted_author

    # Save updated .bib file
    with open(filename, 'w', encoding='utf-8') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)


def load_CSV(filename):#Load the .bib files with bibtexparser then convert to pd df, then convert to CSV 
    with open(filename,"r", encoding='utf-8') as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser()
        bib_database = bibtexparser.load(bibtex_file,parser=parser)
    entries = bib_database.entries
    data_frame = pd.DataFrame(entries)
    data_frame.to_csv('query_results.csv', index=False)
    print(f"Conversion completed! Saved as query_results.csv\nNumber of entries: {len(entries)}")

def bib_file_handler(): #overall function that can be used outside of this file, abbreviate names first, then combine, then create CSV
    abbreviate_author_names("queries/DBLP_query.bib")
    abbreviate_author_names("queries/openalex_query.bib")
    combine_bib_files(["queries/Scopus_query.bib", "queries/DBLP_query.bib", "queries/openalex_query.bib"],"queries/combined_bibs.bib")
    load_CSV("queries/combined_bibs.bib")

#checks if a title is already in that is very similar, only consider titles if year is equal and author is atleast similar
def is_duplicate_entry(new_entry, existing_entry, title_threshold=90):

    title1 = new_entry.get("title", "").lower().strip()
    title2 = existing_entry.get("title", "").lower().strip()
    title_ratio=fuzz.ratio(title1, title2)

    auth1=new_entry.get("author", "").lower().strip()
    auth2=existing_entry.get("author", "").lower().strip()
    auth_ratio=partial_ratio(auth1,auth2)
    #if year is not the same , discard as it cannot be a duplicate, most reliable comparison as all queries
    if new_entry.get("year","").strip()!=existing_entry.get("year","").strip():
        return False
    if new_entry.get("doi") and existing_entry.get("doi") and new_entry.get("doi").lower()!=existing_entry.get("doi").lower() and new_entry.get("doi") !="null" and existing_entry.get("doi")!="null":
        return False
    if auth_ratio > 75 and title_ratio>=title_threshold:
        print(f"Duplicate found: {new_entry.get("ID")} already exists in merged entries: {existing_entry.get("ID")}")
        return True
    return False

def combine_bib_files(input_files,output_file):#combine n bib files which includes is_duplicate_entry() 
    all_entries = []
    scopus_entries=0
    dblp_entries=0
    openAlex_entries=0

    parser = BibTexParser(common_strings=True)
    parser.expect_multiple_parse = True
    writer = BibTexWriter()

    # Load all entries from all files and save as: all_entries
    for file in input_files:
        with open(file, "r", encoding="utf-8") as bibfile:
            bib_data = bibtexparser.load(bibfile, parser=parser)
        all_entries=bib_data.entries
    # search for duplicates:
    merged_entries = []
    seen_dois = set()
    is_duplicate = False
    for new_entry in all_entries:
        new_doi = new_entry.get("doi", "").strip().lower()
        #first check if doi is already present
        if new_doi and new_doi in seen_dois:
            print("Duplicate DOI: ",new_entry.get("ID"))
            continue
        #check if title is already in any existing entries
        is_duplicate = any(
        is_duplicate_entry(new_entry, existing_entry)
        for existing_entry in merged_entries)

        #if no duplicate, add entry to be merges and add DOI so matching can be done 
        if not is_duplicate:
            merged_entries.append(new_entry)
            #increase number of entries for different DB entries
            if  "SCOP" in new_entry.get("ID"): scopus_entries = scopus_entries+1
            elif "DBLP" in new_entry.get("ID"): dblp_entries = dblp_entries+1
            elif "OPAL" in new_entry.get("ID"): openAlex_entries=openAlex_entries+1
            if new_doi:
                seen_dois.add(new_doi)
            

    # Write new file
    merged_db = bibtexparser.bibdatabase.BibDatabase()
    merged_db.entries = merged_entries

    with open(output_file, "w", encoding="utf-8") as bibfile:
        bibfile.write(writer.write(merged_db))
    print(f"without duplicates: \n openalex: {openAlex_entries} , dblp: {dblp_entries}, scopus: {scopus_entries}")
    print(f" Merged {len(merged_entries)} entries into {output_file}")

def test_combine(): #function to test the combine_bib_files function
    combine_bib_files(["test_files/merge_test1.bib", "test_files/merge_test2.bib"],"test_files/test_combined.bib")
    print("Check Test_combined file")
    
    '''test different cases, duplicates and non duplicates
    # only consider DOI for first case
    
    duplicates:
    # 1. exact same entry (with doi) 
    # 2. slighty varied title, one has "." other does not 
    # 3. slighty more varied title,spelling mistake
    # 4. same title but case sensitive
    # 5. same doi but different metadata
    # 6. same doi but case sensitive
    # 7. author name format, abbreviated vs non abbreviated
    # 8. author name spelling mistake
    # 9. author name has special case like ê etc. NOTE Threshold for title needs to be adjusted as a,ä or a,â etc. are marked as differences
    # 10. exact same entry but one has no doi  
    
    non duplicates but similar:
    # 11. Title with Synonyms or Stopword Changes
    # 12. same entry but different year
    # 13. similar title but different author
    # 14. same entry but different doi
    # 15. same title but one has additional text, like an explanation or sth. like that NOTE hard to explain but can be considered as duplicate
    # '''  
def test_auth_abbr():
    ''' 1. no abbreviation, 2 firstname 1 lastname
        2. second firstname abbreviated, first and last name not
        3. first firstname abbreviated, second and last one not
        4. already abbreviated
        5. first name, last name
        6. only lastname (stays, as it should)
@article{RRexportLoryD.Molesky1990,
 author = {Deniz Test Hagelstein},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}

@article{RRexportLoryD.Molesky1990,
 author = {Deniz d. Hagelstein},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
@article{RRexportLoryD.Molesky1990,
 author = {D. Feniz Hagelstein},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
@article{RRexportLoryD.Molesky1990,
 author = {Hagelstein D.D.},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
@article{RRexportLoryD.Molesky1990,
 author = {Deniz Hagelstein},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
@article{RRexportLoryD.Molesky1990,
 author = {Hagelstein},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
@article{RRexportLoryD.Molesky1990,
 author = {Deniz Hagelstein and Test Testcase},
 doi = {},
 journal = {},
 note = {},
 title = {},
 type = {},
 year = {}
}
    ''' 
    abbreviate_author_names("test_files/auth_name_test_file.bib")
    return

