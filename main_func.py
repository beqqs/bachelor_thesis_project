import pandas as pd
from quantitative_analysis import QA_algo
from keybert import KeyBERT
from paper_collection import paper_search
from bib_file_handling import bib_file_handler,load_CSV
import pypdf
import fitz

def extract_text_from_pdf(pdf_path):
  text = ""
  with fitz.open(pdf_path) as doc:
      for page in doc:
          text += page.get_text()
  return text

def extract_texts_from_pdfs(pdf_paths):
    all_texts = {}
    for path in pdf_paths:
        text = extract_text_from_pdf(path)
        all_texts[path] = text
    return all_texts

def load_CSV2():
  csv_df = pd.read_csv('query_results.csv')
  csv_df = csv_df.map(lambda x: x.decode('utf-8', errors='ignore') if isinstance(x, bytes) else x)
  return csv_df

def generate_keywords(text, n_candidates=15):
    # Use a more powerful embedding model
    kw_model = KeyBERT(model='all-mpnet-base-v2')
    #kw_model = KeyBERT()
    # Extract top n_candidates keywords without diversity filtering
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1,1),
        stop_words='english',
        nr_candidates=100,
        top_n=5,
        use_maxsum=False,
        use_mmr=False,
        #diversity=0.90
    )
    # Filter out duplicates and generic terms
    seen = set()
    filtered_keywords = []
    for kw, score in keywords:
        kw_lower = kw.lower()
        if (
            kw_lower not in seen#filter some words..
            and 'keyword' not in kw_lower
            and 'example' not in kw_lower
            and 'using' not in kw_lower
            and 'exist' not in kw_lower
            and 'used' not in kw_lower
            and 'tool' not in kw_lower
            and 'test' not in kw_lower
            and score > 0.17  # keep only "relevant" keywords
        ):
            seen.add(kw_lower)
            filtered_keywords.append(kw)
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(2,2),
        stop_words='english',
        nr_candidates=35,#needs to be reduced so the program terminates
        top_n=5,
        use_mmr=True
    )

    for kw, score in keywords:
        kw_lower = kw.lower()
        if (
            kw_lower not in seen#filter some words..
            and 'keyword' not in kw_lower
            and 'example' not in kw_lower
            and 'using' not in kw_lower
            and 'exist' not in kw_lower
            and 'used' not in kw_lower
            and 'tool' not in kw_lower
            and score > 0.17  # keep only "relevant" keywords
        ):
            seen.add(kw_lower)
            filtered_keywords.append(kw)
    keywords = kw_model.extract_keywords(
      text,
      keyphrase_ngram_range=(3,3),
      stop_words='english',
      nr_candidates=35,#needs to be reduced so the program terminates
      top_n=5,
      use_mmr=True,
      diversity=0.3
  )

    for kw, score in keywords:
        kw_lower = kw.lower()
        if (
            kw_lower not in seen#filter some words..
            and 'keyword' not in kw_lower
            and 'example' not in kw_lower
            and 'using' not in kw_lower
            and 'exist' not in kw_lower
            and score > 0.17  # keep only "relevant" keywords
        ):
            seen.add(kw_lower)
            filtered_keywords.append(kw)    



    return filtered_keywords

def main():
      
  #abstract from the paper: Testing Real-Time Systems Using UPPAAL 
  #https://doi.org/10.1007/978-3-540-78917-8_36
    doc="Testing Real-Time Systems Using UPPAAL. This chapter presents principles and techniques for model-based black-box conformance testing of real-time systems using the Uppaal model-checking tool-suite. The basis for testing is given as a network of concurrent timed automata specified by the test engineer. Relativized input/output conformance serves as the notion of implementation correctness, essentially timed trace inclusion taking environment assumptions into account. Test cases can be generated offline and later executed, or they can be generated and executed online. For both approaches this chapter discusses how to specify test objectives, derive test sequences, apply these to the system under test, and assign a verdict."
    kwds=generate_keywords(doc)
    new_kwds=[]
    i=0
    print("----generating keywords----")
    for kwd in kwds:
      i+=1
      print(i,kwd)
    print("please select up to three of these keywords by typing in the index:")
    while len(new_kwds)<=3:
      if new_kwds != []: print("Keywords for query:",new_kwds)
      opt=input("type in an index of a keyword you would like to enter or enter '' when done:  ")
      if opt=='':break
      try:
        opt=int(opt)
      except ValueError:
         print("not an index!")
         continue
      if not int(opt) or opt > i:
        print("invalid input") 
        return
      else:
        print(f"selected keyword:{opt} : {kwds[opt-1]}")
        new_kwds.append(kwds[opt-1])
#    amount_kwds=int(input("\nHow many Keywords would you like to have? 1-2"))
    
    #doc=extract_text_from_pdf("PDF_files/papers/init_paper.pdf")
    if len(new_kwds) < 1:return
    decision="  "

    while decision != "":
      for kwd in new_kwds:
        print("Keyword:",new_kwds.index(kwd)+1,"is:",kwd)
      decision=input("Do you want to change a Keyword?\ny/n?: ")
      if decision =="y":
          decision=input("Which one would you like to change?\ntype '1'/'2'' or '' if youre done: ")
          if decision =="":
            print("keyword editing canceled!")
            break
          elif decision == 1 or 2  :
            decision=int(decision)
            print("you want to change:",new_kwds[decision-1])
            new_kwds[decision-1]=input("type in new Keyword: ")
          else:
             print("wrong input!")
      elif decision=="n":
         break 
      else:
         print("wrong input!")
    print("Query will be done with Keywords:",new_kwds)

    print("----attempting to search papers----")
    paper_distribution=paper_search(new_kwds)#do paper queries and save the amount of elements in a list
    print("----papers searched and saved----")
    print("----attempting to format bib files----")
    bib_file_handler() #merge bib files and create CSV
    print("----successfully formatted bib files----")
    print("----Attempting to loading CSV data----")
    csv_df = load_CSV2()#load csv
    print("----Successfully loaded CSV data----")
    print("----attempting quantitative analysis----")
    QA_algo(csv_df,paper_distribution)#use csv and paper distribution to perform QA
    print("----successfully done quantitative analysis----")


if __name__ == "__main__":
    main()