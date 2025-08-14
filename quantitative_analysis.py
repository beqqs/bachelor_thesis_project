import pandas as pd #needed for working with CSV files
import matplotlib.pyplot as plt #needed for plotting graphs later
import math
import re
import numpy as np
from collections import defaultdict, Counter
from pypdf import PdfWriter

#some journal names are over 45 character, shorten the words and delete stop words for readability
def abbreviate_journal(name):
    if not isinstance(name, str):
        return name

    if len(name) > 25:
        stopwords = {'of', 'the', 'and', 'in', 'on', 'for', 'with', 'to', 'a'}
        words = re.findall(r'\b\w+\b', name)#filter words out of string

        abbrev_parts = []
        for word in words:
            lower_word = word.lower().strip()
            if lower_word in stopwords:
                continue
            elif lower_word == "journal":
                abbrev_parts.append("J.")
            elif len(word) > 5:
                abbrev_parts.append(word[:3] + ".")
            else:
                abbrev_parts.append(word)

        return ' '.join(abbrev_parts)

    return name
def mergePDF():
   folder = "PDF_files"
   pdfs = [
         "papers_per_author.pdf",
         "publications_per_journal.pdf",
         "yearly_trend.pdf",
         "number_of_citations.pdf",
         "type_of_publications.pdf",
         "most_cited_papers.pdf",
         "paper_distribution.pdf"
           ]
   pdf_paths = [f"{folder}/{pdf}" for pdf in pdfs]
   merger = PdfWriter()
   for pdf in pdf_paths:
      merger.append(pdf)

   print("Quantitative analysis has been done!\nSee Quantitative_Analysis_Result.pdf for the results")
   merger.write(f"{folder}/Quantitative_Analysis_Results.pdf")
   merger.close()

#get citations from note field, in case there is something in the note fiel that is not a number
#step can pbbly omitted since i only save numbers in note field
def extract_citations(note): 
   if isinstance(note, str):
        match = re.search(r'cited by[:\s]*([0-9]+)', note.lower())
        if match:
            return int(match.group(1))
   elif note!=0:
      return note
   return 0  

# functions for analysis
def most_cited_papers(csv_df):
   csv_df['citations'] = csv_df['note'].apply(extract_citations)
   top_cited = csv_df.sort_values(by='citations', ascending=False).head(10)
   table_data = top_cited[['title', 'author', 'year', 'citations']].reset_index(drop=True)
   columns=['Title', 'Author', 'Year', 'Citations']
   
   #plot
   plt.figure(figsize=(12,8))
   table = plt.table(cellText=table_data.values.tolist(), loc='center', colLabels=columns, cellLoc='left')
   table.auto_set_font_size(False)
   table.auto_set_column_width(12)
   for key, cell in table.get_celld().items():
      cell.set_fontsize(6.5)
   plt.axis("off")
   table.scale(1.3, 1.5)
   table.auto_set_column_width(col=list(range(4)))
   plt.title("Most Cited Papers")
   table.scale(1.25,1.6) 
   plt.savefig("PDF_files/most_cited_papers.pdf", format="pdf",dpi=400)
   plt.savefig("PDF_files/most_cited_papers.png", format="png")
   plt.close()
   return 0

def number_citations(csv_df):
    # bin values, bin labels and colors
   max_citation = csv_df['note'].max()
   if max_citation < 500:
      bins = [0, 10, 50, 100, 200, float('inf')]
   elif max_citation < 200000:
      bins = [0, 35, 75, 125, 250, 500, float('inf')]
   else:
      bins = [0, 50, 100, 200, 500, 1000, 2000, float('inf')]
   bin_labels = [f"{bins[i]}–{bins[i+1]-1}" if bins[i+1] != float('inf') else f"{bins[i]}+"for i in range(len(bins)-1)]

   types = csv_df['type'].unique()  # e.g., ['InProceedings', 'Journal', 'Book']
   type_colors = ['skyblue', 'salmon', 'lightgreen','blue']  # Must match the number of types

   # Initialize counts: a dict of {type: [bin_counts]}
   grouped_counts = {t: [0] * (len(bins) - 1) for t in types}

   for _, row in csv_df.iterrows():
      citation = row['note'] #contains only a number, made sure at paper collection
      t = row['type']

      if isinstance(citation, (int, np.integer)):
         for i in range(len(bins) - 1):
               if bins[i] <= citation < bins[i + 1]:
                  grouped_counts[t][i] += 1
                  break
      elif citation != 0:
         print(type(citation), "error: wrong type in 'note' column, PLEASE CHECK")

    # Plotting
   x = np.arange(len(bin_labels))  # positions for groups
   bar_width = 0.25  # Width of each bar

   plt.figure(figsize=(12, 8))

   for i, t in enumerate(types): #plot all the 3 bars
      offsets = x + (i - len(types)/2) * bar_width + bar_width/2
      bars = plt.bar(offsets, grouped_counts[t], width=bar_width,
                     label=f"Type {t}", color=type_colors[i], edgecolor='black')

      # Add bar value labels
      for bar, count in zip(bars, grouped_counts[t]):
         height = bar.get_height()
         plt.text(bar.get_x() + bar.get_width()/2, height + 1, f"({count})",
                  ha='center', va='bottom', fontsize=9)

   plt.xticks(x, bin_labels)
   plt.xlabel("N citations")
   plt.ylabel("N Publications")
   plt.title("Citations per Paper by Type")
   plt.legend(title="Type")
   plt.tight_layout()
   plt.savefig("PDF_files/number_of_citations.pdf", format="pdf")
   plt.savefig("PDF_files/number_of_citations.png", format="png")
   plt.close()


def publications_per_journal(csv_df):
    csv_df['journal_abbrev'] = csv_df['journal'].apply(abbreviate_journal)
    # Apply normalization


    # Count publications per normalized journal
    journal_counts = csv_df.groupby('journal_abbrev').size()

    # Group journals with less then "X" publication into "Other"
    main_journals = journal_counts[journal_counts > 6]
    other_count = journal_counts[journal_counts <= 6].sum()

    # Append "Other" category
    final_counts = main_journals.copy()
    if other_count > 0:
        final_counts['Less than 6 papers'] = other_count

    # Sort descending
    final_counts = final_counts.sort_values(ascending=False)

    # Plot
    plt.figure(figsize=(12, 8))
    plt.bar(final_counts.index, final_counts.values,  color='skyblue', edgecolor='black')
    for i , v in enumerate(final_counts.values):
        plt.text(i,v+2,"(%d)" %v, ha="center")
    plt.title("Publications per Journal")
    plt.ylabel("N Publications")
    plt.xlabel("Journal")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("PDF_files/publications_per_journal.pdf", format="pdf")
    plt.savefig("PDF_files/publications_per_journal.png", format="png")
    plt.close()

def yearly_trend_by_type(csv_df):

   # Group by type and year, count number of publications
   grouped = csv_df.groupby(['type', 'year']).size().unstack(fill_value=0)
   total_per_year = grouped.sum(axis=0)
   
   #-plotting-#
   plt.figure(figsize=(12, 8))
   
   #plot all types#
   for pub_type in grouped.index:
      years = grouped.columns
      counts = grouped.loc[pub_type]
      plt.plot(years, counts, marker='o', linestyle='-', label=pub_type)
   #plot total#
   plt.plot(total_per_year.index, total_per_year.values, 
      marker='s', linestyle='--', color='b', linewidth=2, label='Total')

   plt.xticks(grouped.columns, rotation=45)
   plt.title("Yearly Trend of Publications by Type")
   plt.ylabel("N Publications")
   plt.xlabel("Year")
   plt.legend(title="Publication Type")
   plt.tight_layout()

   plt.savefig("PDF_files/yearly_trend.pdf", format="pdf")
   plt.savefig("PDF_files/yearly_trend.png", format="png")
   plt.close()

   return 0

def papers_per_author(csv_df): 
   all_authors = []
   for author_entry in csv_df['author'].dropna():
      # Split on " and " if more than one author, then strip leading/trailing spaces
      names = [name.strip() for name in re.split(r"\s+and\s+", author_entry)]
      all_authors.extend(names)

   # Count number of publications per author
   author_counter = Counter(all_authors)
   # Count how many authors have published X papers
   pub_count_distribution = Counter(author_counter.values())

   x = sorted(pub_count_distribution.keys())
   y = [pub_count_distribution[k] for k in x]

   # Plotting
   plt.figure(figsize=(12, 8))
   plt.bar(x, y,  color='skyblue', edgecolor='black')
   for xi, yi in zip(x, y):
      plt.text(xi, yi+2, "(%d)" % yi, ha="center")
   plt.title("Publications per Author")
   plt.ylabel("N Authors")
   plt.xlabel("N Publications")
   plt.savefig("PDF_files/papers_per_author.pdf", format="pdf")
   plt.savefig("PDF_files/papers_per_author.png", format="png")
   plt.close()


   return 0

def type_of_publications(csv_df):
   types_of_publications = csv_df.groupby('type').size()
   x = types_of_publications.index  # publication types
   y = list(types_of_publications.values)  # counts
   total = sum(y)

   # Function to show the actual count on each slice
   def absolute_value(val):
      a = int(round(val / 100 * total))
      return a

   # Plotting
   plt.figure(figsize=(12, 8))
   plt.title(f"Types of Publication (Total: {total})")
   plt.pie(y, labels=x, autopct=absolute_value)
   plt.tight_layout()

   # Save files
   plt.savefig("PDF_files/type_of_publications.pdf", format="pdf")
   plt.savefig("PDF_files/type_of_publications.png", format="png")
   plt.close()

   return 0

def paper_distribution_graph(paper_distribution):
   y=[int(i) for i in paper_distribution] #DBLP then Scopus then OpenAlex
   x=["DBLP","SCOPUS","OpenAlex"]
   plt.figure(figsize=(12, 8))
   plt.bar(x,y,color='skyblue', edgecolor='black')
   for i, value in enumerate(y):
      plt.text(i, value + 1, f"({value})", ha='center', va='bottom', fontsize=12)
   plt.title("Publications per Database")
   plt.ylabel(f"N Publications ({sum(y)})")
   plt.xlabel("Database")
   plt.xticks(rotation=45, ha='right')
   plt.ylim(bottom=0)
   plt.savefig("PDF_files/paper_distribution.pdf", format="pdf")
   plt.savefig("PDF_files/paper_distribution.png", format="png")
   plt.close()
   return

#func get csv df and then do QA algos, merge pdfs in the end
def QA_algo(csv_df,paper_distribution):
   most_cited_papers(csv_df)
   number_citations(csv_df) 
   type_of_publications(csv_df)
   yearly_trend_by_type(csv_df)
   publications_per_journal(csv_df)
   papers_per_author(csv_df) 
   paper_distribution_graph(paper_distribution)
   mergePDF()
   return 0
# csv_df = pd.read_csv('RR_results.csv')
# csv_df = csv_df.map(lambda x: x.decode('utf-8', errors='ignore') if isinstance(x, bytes) else x)
# QA_algo(csv_df,[0,0,0])
# number_citations(csv_df)
# titles = csv_df.get('title')
# years=csv_df.get('year')
# types=csv_df.get('type')
# notes=csv_df.get('note')
# dois=csv_df.get('doi')
# entrytypes=csv_df.get('ENTRYTYPE')
# IDs=csv_df.get('ID')
# #year,type,title,note,journal,doi,author,ENTRYTYPE,ID

# print(len(titles) , len(years), len(years), len(dois),len(entrytypes), len(IDs) )