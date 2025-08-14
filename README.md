This is the Project for the Bachelor Thesis of Deniz Hagelstein
The title of this thesis is: 
"Quantitative Evaluation of AI-based Literature Search in Comparison to Systematic Literature Search"
This project aims to provide a Systemtic literature search by querying 3 databases and comparing it to an AI approach.
To use the programs of this project, please follow the instructions.
# How to use:
### SLS:
You execute the main function and follow the instructions in the console.
At the end you will have new files in the queries folder which are the results of the queries and you will have new files in the PDF_files folder for the Quantitative analysis.
### AI search:
The export data for the mentioned input papers is saved in the queries folder.
The export of the AI query for the initial paper is called RR_export_new.bib, for the test cases the files are named with the number of the test case.
if a new AI query is to be done, registration at Research Rabbit is neccessary.
The file ai_handling.py does all the functions for searching for similarities, however the functions need to be executed.
If you want to reproduce the title matches or data enrichement you need to change the code so that the functions are executed with the desired input.
###
testing files are in the test_files folder, merge and author abbreviation test can be done from the bib_file_handlind.py.

### requirements:
1. make sure all the required libraries are installed, for that use:
"pip install -r requirements.txt"
2. you also NEED to be in the university VPN to access more than 25 scopus results, otherwise the Scopus search will abort and the program gets terminated
3. the API key for Scopus may expire in the future, keep that in mind or use another one in the paper_collections.py
for that you need to change the global variable: "SCOPUS_API_KEY= XXXXX " to your key

written and created by Deniz Hagelstein