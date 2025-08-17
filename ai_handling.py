import bibtexparser
from bibtexparser.bparser import BibTexParser
import pandas as pd
import time
import requests
from bibtexparser.bwriter import BibTexWriter
from rapidfuzz.fuzz import token_set_ratio
from rapidfuzz.fuzz import partial_ratio
from quantitative_analysis import QA_algo
from paper_collection import clean_up_type
from bib_file_handling import abbreviate_author_names
import bibtexparser
from rapidfuzz import fuzz, process
import json
def load_titles_from_bib(file_path):#load titles from bib file as list
    with open(file_path, encoding='utf-8') as bib_file:
        bib_database = bibtexparser.load(bib_file)
    return [entry['title'].lower() for entry in bib_database.entries if 'title' in entry]

def load_doi(file_path):#load dois from a bib file as list
    with open(file_path, encoding='utf-8') as bib_file:
        bib_database = bibtexparser.load(bib_file)
    return [entry['doi'] for entry in bib_database.entries if 'doi' in entry]

def load_author(file_path):#load authors from a bib file as list
    with open(file_path, encoding='utf-8') as bib_file:
        bib_database = bibtexparser.load(bib_file)
    return [entry['author'] for entry in bib_database.entries if 'author' in entry]

def compare_titles(file1, file2, threshold=90):#function for finding matched between AI and non AI bib files
    titles1 = load_titles_from_bib(file1)
    print(len(titles1))
    titles2 = load_titles_from_bib(file2)
    print(len(titles2))

    matches = []

    for t1 in titles1:
        best_match = process.extractOne(
            t1,
            titles2,
            scorer=fuzz.ratio
        )
        if best_match and best_match[1] >= threshold:
            matches.append({
                'title_1': t1,
                'title_2': best_match[0],
                'score': best_match[1]
            })

    return matches

def append_results(author,doi,journal,note,title,type,year):#this function APPENDS to the RR_new.bib file, so you need to clear the file before 
    entry = f"@article{{RRexport{author.replace(" ","")}{year},\n" \
             f"  author = {{{author}}},\n" \
             f"  title = {{{title}}},\n" \
             f"  journal = {{{journal}}},\n" \
             f"  year = {{{year}}},\n" \
             f"  note = {{{note}}},\n" \
             f"  type = {{{type}}},\n" \
             f"  doi = {{{doi}}}\n" \
             f"}}\n\n"
    
    with open("RR_new.bib", "a", encoding="utf-8") as bibfile:
        bibfile.write(entry)
def auth_match_func(RRauth,OLauth):
    for auth in RRauth:
        for auth2 in OLauth:
            if partial_ratio(auth,auth2)> 85:
                return True
    return False
            

def new_fetch_info():
    no_matches=0
    with open("queries/RR_export_new.bib", encoding='utf-8') as bibfile:
        bib_data = bibtexparser.load(bibfile)
        all_entries=bib_data.entries
    for entry in all_entries:#get data from RRexport
        match_found=False
        #time.sleep(0.2)
        RRyear=entry.get("year")
        RRdoi=entry.get("doi")
        RRtitle=entry.get("title").replace(",","").replace("!","").replace("?","").replace("&","").replace(":","").strip()
        RRtitle_raw=entry.get("title").strip().replace(".","").lower()
        RRauthors=entry.get("author").split("and")#get all authors to later search for matches
        #api request with title
        url = (
            f"https://api.openalex.org/works?filter=title.search:{RRtitle}"
            f",type_crossref:journal-article|proceedings-article"
            f",has_oa_accepted_or_published_version:true"
        )
        #url=f"https://api.openalex.org/works?filter=title.search:{RRtitle}&filter=is_indexed_in_scopus:true|is_in_doaj:true" #raw title has some characters that cannot be entered in a url -> use rrtitle
        response=requests.get(url)
        if response.status_code != 200:#check if response is valid
            print(url)
            print(f"API request failed: {response.status_code}, {response.text}")
            continue #go to next entry
        data=response.json()
        works=data.get('results')
        matchFound=False
        for work in works:#3 cases
            OLtitle=work.get("title").strip().replace(".","").lower()
            OLyear=str(work.get("publication_year"))
            all_authors = []
            for authorship in work['authorships']:
                name = authorship['raw_author_name']
                all_authors.append(name)
            doi = work.get('doi', '')
            if doi != None: 
                doi=doi[16:]
            score=0
            title_similarity=fuzz.ratio(OLtitle,RRtitle_raw)
            if title_similarity > 90:score+=2
            if auth_match_func(RRauthors,all_authors):score+=1
            if doi == RRdoi and RRdoi != None:score += 2 #best indicator, if present
            if OLyear == RRyear :score += 1
            if OLyear != RRyear :score -= 1
            
            if score > 3:
                matchFound=True
                author = work.get('authorships', [])[0]['raw_author_name'] if work.get('authorships') else 'Unknown Author'
                primary_location = work.get('primary_location')
                journal = 'Unknown Venue'
                if isinstance(primary_location, dict):
                    source = primary_location.get('source')
                    if isinstance(source, dict):
                        journal = source.get('display_name', 'Unknown Venue')

                    note = work.get("cited_by_count", "0")
                    pbtype= work.get('type_crossref', "").strip()
                    pbtype=clean_up_type(pbtype)
                    break 
        if not matchFound:
            print("no match found for ",RRtitle_raw)
            no_matches+=1
            print(url)
            continue
        else:
            append_results(author,doi,journal,note,RRtitle_raw,pbtype,OLyear)
            continue
    print(f"out of the {len(all_entries)} RR export entries,  {no_matches} matches were not found.")

def fetch_info():#get info from openAlex depending on DOI This is deprecated, use the new fetch function-
    with open("queries/RR_export_new.bib", encoding='utf-8') as bibfile:
        bib_data = bibtexparser.load(bibfile)
        all_entries=bib_data.entries
        print(len(all_entries))
    for entry in all_entries:#get data from RRexport
        time.sleep(0.2)
        RRdoi = entry.get("doi")
        RRyear=entry.get("year")
        RRtitle=entry.get("title").replace(",","").replace("!","").replace("?","").replace("&","").strip()#openAlex does not accept "," or "!"...
        RRtitle_raw=entry.get("title").strip().replace(".","").lower()
        RRjournal=entry.get("journal")
        if RRjournal =="null": RRjournal="Unknown Venue"
        author,title,year,note,type="","","","","" #variables for saving w/ RRdoi
        RRauthor=entry.get("author").split("and")
        RRauthor=RRauthor[0].strip()
        if RRdoi=="null":#DOI not in RR export, fetch data with title
            RRdoi=""
            #api request with title
            url=f"https://api.openalex.org/works?filter=title.search:{RRtitle}"
            response=requests.get(url)
            if response.status_code != 200:#check if response is valid
                print(url)
                print(f"API request failed: {response.status_code}, {response.text}")
                continue
            data=response.json()
            works=data.get('results')
            matchFound=False
            
            #go through all the titles found and search for the one where year and title are matching
            for work in works:#3 cases
                OLtitle=work.get("title").strip().replace(".","").lower()
                OLyear=str(work.get("publication_year"))
                
                if OLtitle != RRtitle_raw:#case 1 : title does not match at all, ignore
                    continue
                elif OLtitle == RRtitle_raw and OLyear == RRyear:#case 2: title and year match -> match, allocate variables
                    matchFound=True
                    author=work.get('authorships', [])[0]['raw_author_name'] if work.get('authorships') else 'Unknown Author'
                    author=author.replace(",","")
                    title=OLtitle
                    raw_type=work.get('type_crossref', "").strip()
                    type=clean_up_type(raw_type)
                    year=OLyear
                    new_doi=work.get('doi', '')
                    if new_doi != None: 
                        new_doi=new_doi[16:]
                    else: new_doi =RRdoi
                    primary_location = work.get('primary_location')
                    note=work.get("cited_by_count", "0")
                    if isinstance(primary_location, dict):
                        source = primary_location.get('source')
                        if isinstance(source, dict):
                            venue = source.get('display_name', 'Unknown Venue')
                    journal = venue
                    append_results(author,new_doi,journal,note,title,type,year)
                    break
                else:
                    continue #case 3: title matches but year does not: not a match, ignore
            #if no match in the works found, save as RR export
            if not matchFound:
                print("no match found for ",RRtitle)
                append_results(
                author=RRauthor,
                doi=RRdoi,
                journal=RRjournal,
                note="0",
                title=RRtitle_raw,
                type="Unknown",
                year=RRyear)
            else:continue # get to next RR entry, since its already saved in case 2

        else:# DOI exists in RRexport:
            #api request
            url=f"https://api.openalex.org/works/https://doi.org/{RRdoi}"
            response=requests.get(url)
            if response.status_code != 200:#check if response is valid
                print(url)
                print(f"API request failed: {response.status_code}, {response.text}")
                continue
            data=response.json()
            
            #get data from json
            venue = 'Unknown Venue'
            primary_location = data.get('primary_location')
            raw_type=data.get('type_crossref', "").strip()
            type=clean_up_type(raw_type)
            if isinstance(primary_location, dict):
                source = primary_location.get('source')
                if isinstance(source, dict):
                    venue = source.get('display_name', 'Unknown Venue')
            
            author=data.get('authorships', [])[0]['raw_author_name'] if data.get('authorships') else 'Unknown Author'
            author=author.replace(",","")
            journal=venue
            note=data.get('cited_by_count', "0")
            title=data.get('title')
            if title==None:title=RRtitle #just in case if the title from the openAlex Query is missing, use from RR export
            year=data.get('publication_year', '')
            append_results(author,RRdoi,journal,note,title,type,year)
        

def load_CSV():#open the .bib file with bibtexparser then convert to pd df, then convert to CSV 
    with open("RR_new.bib","r", encoding='utf-8') as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser()
        bib_database = bibtexparser.load(bibtex_file,parser=parser)
    entries = bib_database.entries
    data_frame = pd.DataFrame(entries)
    data_frame.to_csv('RR_results.csv', index=False)
    print(f"Conversion completed! Saved as query_results.csv\nNumber of entries: {len(entries)}")