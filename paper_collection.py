import requests
import csv
import json
from datetime import datetime
from urllib.parse import quote
import time

SCOPUS_API_KEY = 'da5602c0c98f85685927faa1e4e101d3'
SCOPUS_BASE_URL ='https://api.elsevier.com/content/search/scopus'

def search_openalex(kwd, max_results=2000):
    base_url = "https://api.openalex.org/works"
    per_page = 200
    cursor = "*"
    all_works = []
    count = 0
    bib_entries = []

    while True:
        url = (
            f"{base_url}?search=({kwd})"
            f"&filter=type_crossref:journal-article|proceedings-article,"
            f"has_oa_accepted_or_published_version:true"
            f"&per-page={per_page}&cursor={cursor}"
        )
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code}, {response.text}")

        data = response.json()
        works = data.get('results', [])
        meta = data.get('meta', {})

        if not works:
            break

        all_works.extend(works)
        count += len(works)

        # Optional limit
        if max_results and count >= max_results:
            all_works = all_works[:max_results]
            break

        cursor = meta.get('next_cursor')
        if not cursor:
            break

        time.sleep(0.3)  # to not overload api

    # Save bib file
    with open("queries/openalex_query.bib", 'w', encoding='utf-8') as bibfile:
        for i, work in enumerate(all_works):
            primary_location = work.get('primary_location')
            venue = 'Unknown Venue'
            if isinstance(primary_location, dict):
                source = primary_location.get('source')
                if isinstance(source, dict):
                    venue = source.get('display_name', 'Unknown Venue')

            authors = work.get('authorships', [])[0]['raw_author_name'] if work.get('authorships') else 'Unknown Author'
            year = work.get('publication_year', 'n.d.')
            title = work.get('title', 'No Title')
            doi = work.get('doi', '')[16:]  # trim https://doi.org/
            citation_count = work.get('cited_by_count', 0)
            pub_type = work.get('type_crossref', "").strip()
            pub_type = 'Journal' if pub_type == 'journal-article' else 'InProceedings' if pub_type == 'proceedings-article' else pub_type

            bibfile.write(f"@article{{OPAL{i},\n"
                          f"  title = {{{title}}},\n"
                          f"  author = {{{authors}}},\n"
                          f"  year = {{{year}}},\n"
                          f"  journal = {{{venue}}},\n"
                          f"  doi = {{{doi}}},\n"
                          f"  type = {{{pub_type}}},\n"
                          f"  note = {{{citation_count}}}\n"
                          f"}}\n\n")

    print(f"Saved {len(all_works)} entries to queries/openalex_query.bib")
    return len(all_works)

def clean_up_type(raw_type):
    type_mapping = {
    #SCOPUS AND DBLP
    "Journal Articles": "Journal",
    "Conference and Workshop Papers": "InProceedings",
    "Conference Proceeding": "InProceedings",
    "Conference Paper":"InProceedings",
    "Book Series": "Book",
    "Books and Theses": "Book",
    "Journal":"Journal",
    "Book":"Book",
    "Review":"Journal",
    "Article":"Journal",
    "Note":"Journal",
    "Conference Review":"Book",
    "None":"Unknown",
    #OPENALEX:
    "book":"Book",
    "proceedings-article":"InProceedings",
    "reference-book":"Book",
    "monograph":"Journal",
    "book-chapter":"Book",
    "other":"Unknown",
    "unknown":"Unknown",
    "edited-book":"Book",
    "monograph":"Book",
    "journal-article":"Journal"

    }
    standardized_type = type_mapping.get(raw_type)
    if not standardized_type:
        standardized_type="Unknown"
    else: 
        standardized_type = type_mapping.get(raw_type)
    return standardized_type

def search_DBLP(kwd): 
#contains non peer reviewed papers that are filtered in the bib file handler
#parameters for api
    temp=kwd
    print("Please choose a keyword for DBLP from the inserted keywords: ",temp)
    user_input=input("")
    kwd=[]
    while len(kwd)< 2:
        try: 
            user_input=int(user_input)
        except ValueError:
            print("wrong input!")
        kwd=temp[user_input-1]
        break

    url = f'https://dblp.org/search/publ/api?q={kwd}&h={1000}&format=json' 
    response = requests.get(url)
    data =response.json()
    if response.status_code == 200:
        save_json(data,"DBLP_query.json")
    else:
        print(f"Fehler: {response.status_code}")
        return None
    
    count=0
    with open("queries/DBLP_query.json") as json_data:#incase i dont want to do a query or DBLP is not responding,take old json response
        data=json.load(json_data)
#extract data from json
    hits = data["result"]["hits"].get("hit", [])
    with open("queries/DBLP_query.bib", 'w', encoding='utf-8') as f:
        for i, hit in enumerate(hits):
            info = hit.get("info", {})
            key = info.get("key", f"dblp{i}")
            key=f"DBLP_{key}"
            title = info.get("title", "No Title")
            venue = info.get("venue", "")
            year = info.get("year", "n.d.")
            doi = info.get("doi", "")
            paper_type = str(info.get("type", "")).strip()
            paper_type =clean_up_type(paper_type)
            if paper_type =="Unknown":
                print(title)
                continue
            authors_raw = info.get("authors", {}).get("author", []) #only save first author
            if isinstance(authors_raw, dict):  
                authors = [authors_raw.get("text", "")] #single entry, just take the author
            elif isinstance(authors_raw, list) and authors_raw:
                authors = [authors_raw[0].get("text", "")] #list of authors, take first one
            else:
                authors =["noAuthorGiven_CHECK-HERE"]
                print("Error, no author found") 

# Write bibtex entry
            f.write(f"@article{{{key},\n")
            f.write(f"  title = {{{title}}},\n")
            f.write(f"  author = {{{' and '.join(authors)}}},\n")
            f.write(f"  journal = {{{venue}}},\n")
            f.write(f"  year = {{{year}}},\n")
            f.write(f"  doi = {{{doi}}},\n")
            f.write(f"  note = {{0}},\n")
            f.write(f"  type = {{{paper_type}}}\n")
            f.write("}\n\n")
            count=count+1
    print(f"DBLP Query has been saved as .bib file\nTotal number of DBLP results before cleanup: {len(hits)}\nAfter cleanup: {count}")
    return count

def search_scopus(kwd, api_key=SCOPUS_API_KEY, max_results=2000, batch_size=200):
    url = 'https://api.elsevier.com/content/search/scopus'
    headers = {'X-ELS-APIKey': api_key, 'Accept': 'application/json'}

    all_entries = []
    start = 0

    while True:
        params = {
            "query": f'TITLE-ABS-KEY({kwd})', #Options : TITLE-ABS-KEY() / ALL()
            "count": batch_size,
            "start": start,
            "sort": "citedby-count,relevancy"
        }
        print(url,headers,params)
        response = requests.get(url, headers=headers, params=params)
        if response.status_code !=200:
            raise Exception(f"Scopus API request failed: {response.status_code}, {response.text}")

        data = response.json()
        if start == 0:
            save_json(data, "Scopus_query.json")  # Save the first page for inspection

        entries = data.get('search-results', {}).get('entry', [])
        total_results_str = data.get('search-results', {}).get('opensearch:totalResults', '0')
        total_results = int(total_results_str)

        all_entries.extend(entries)
        start += len(entries)

        if max_results and len(all_entries) >= max_results:
            all_entries = all_entries[:max_results]
            break

        if len(entries) < batch_size or start >= total_results:
            break

        time.sleep(0.3)  # Prevent overloading the API

    print(f"Scopus query total results reported: {total_results}")
    count = scopus_save_to_bib(all_entries, "queries/Scopus_query.bib")
    return count

def scopus_save_to_bib(entries, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        count=0
        for i, entry in enumerate(entries):
            key_author = entry.get('dc:creator', 'unknown').split(',')[0]
            key_year = entry.get('prism:coverDate', '')[:4] #only want the year not the month i.e. first 4 numbers
            key_citations =f"{entry.get('citedby-count', '')}"
            key = f"SCOP{key_author}{key_year}{i}"
            key_citations=key_citations.strip()
            key= "".join(key.split())
            paper_type= entry.get('subtypeDescription','')
            paper_type=clean_up_type(paper_type)
            if paper_type =="Unknown":
                paper_type= entry.get('prism:aggregationType','')
                paper_type=clean_up_type(paper_type)
            if paper_type =="Unknown":
                print("no type was found", key)
                continue
            f.write(f"@article{{{key},\n")
            f.write(f" author = {{{entry.get('dc:creator', 'Unknown')}}},\n")
            f.write(f" doi = {{{entry.get('prism:doi', '')}}},\n")
            f.write(f" journal = {{{entry.get('prism:publicationName', '')}}},\n")
            f.write(f" note = {{{key_citations}}},\n")
            f.write(f" title = {{{entry.get('dc:title', '')}}},\n")
            f.write(f" type = {{{paper_type}}},\n")
            f.write(f" year = {{{key_year}}}\n")
            f.write("}\n\n")
            count =count+1
    print("Number of entries saved: ",count)
    return count

#save the individual responses as JSON if the number of queries is limited
def save_json(data, filename):
    path =f"{"queries"}/{filename}"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def paper_search(kwds):
    scopus_kwds= ' AND '.join([f'"{kw}"' for kw in kwds])
    dblp_kwds= kwds#'|'.join([f'"{kw}"' for kw in kwds])
    print("USED KEYWORDWS:   ")
    print("DBLP:",dblp_kwds)
    print("Scopus and OpenALex:   ",scopus_kwds)
    userinput=input("Do you want to start a Query? y/n ")
    
    if userinput == "y":
        paper_distribution=[]    
        dblp_count=search_DBLP(dblp_kwds)
        scopus_count=search_scopus(scopus_kwds)
        openalex_count=search_openalex(scopus_kwds)
        paper_distribution.append(dblp_count)
        paper_distribution.append(scopus_count)
        paper_distribution.append(openalex_count)
        print("total number of results saved in bib file: ",openalex_count,dblp_count,scopus_count)
    else:
        print("No query started")
        return
    return paper_distribution
