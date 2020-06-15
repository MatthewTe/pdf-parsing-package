# PDF Ingestion and Data Transformation Package with PyPDF2 and pdfplumber
* [Table of Contents Extraction](https://github.com/MatthewTe/pdf-parsing-package#table-of-contents-extraction)
* [Instillation Instructions](https://github.com/MatthewTe/pdf-parsing-package#instillation-instructions)
* [Text Extraction](https://github.com/MatthewTe/pdf-parsing-package#text-extraction)
* [Search Method](https://github.com/MatthewTe/pdf-parsing-package#search-method)
* [PDF Sqlite Database API](https://github.com/MatthewTe/pdf-parsing-package#sqlite-database-api)

### Instillation Instructions
The package can be directly installed via the pip package manager:
```
pip install git+https://github.com/MatthewTe/pdf-parsing-package.git
```
If dependencies are not automatically installed they can be manually installed as the packages are relatively lightweight:
```
pip install pandas
pip install PyPDF2
pip install pdfplumber
pip install nltk
pip install Dash
```

### PDF Ingestion
The ingestion of pdfs are mainly done via the PyPDF2 and the pdfplumber libraries.
 The structure of the main pdf object is as follows:

- The Table of Contents that contains a list of all the pdf sections and nested
sub-sections with their respective page ranges is built using the PyPDF2 library
to extract all Destination objects of the pdf. The page ranges of these Destinations
are determined via a rage range detection algorithm described below.

- The pdfplumber library is then used to extract the text and tables from the pdf
and indexes said tables and text by the range of each pdf section.       

The pdf_ingestion_engine is structured as a module designed to ingest a PDF via
a file path and transform said PDF into text data indexed by financial report
sections to be fed into other applications that require structured textual data
such as natural language processing.  


### Table of Contents Extraction:
The first step to implementing the lazy prices algorithm is to extract the table
of contents from a financial statement.

Currently this is done via PyPDF2. The library allows you to extract a Destination
objects. PDF Destinations are ["a named page view"](https://www.evermap.com/Tutorial_ABM_Destinations.asp). It associates a unique name with
a specific page location within a PDF document. In practice this is what allows
bookmark functionality in a pdf viewer. The PyPDF2 library allows for the extraction
of a pdf's outline as a [nested list of Destination objects](https://pythonhosted.org/PyPDF2/PdfFileReader.html) Through the `.getOutlines()` method.

A list of these nested destination objects is initialized by an internal method and this list is passed into another method where each destination in the list is modified to include each respective page range:

```python
self.destination_lst = []

# Methods modify self.destination_lst
self.pop_destination_lst(self.getOutlines, counter=0) # populates w/ destinations
self.build_toc(self.destination_lst) # Modifies to include page ranges.
```

The page ranges for each destination dictionary are determined by a very simplistic "algorithm". As stated in the documentation, PyPDF2 returns a
nested list of dictionaries that would also indicate on what level or sub-level each Destination is on. The `self.pop_destination_lst()` method recursively extracts each nested list into a single list, with a int variable instead indicating the level said dict occupied in the "nest".

The page ranges were calculated by operating at the lowest level of the "nest" first. Due to this it was then assumed that the end page of a section would be the start page of the next section in the list. Once all the page ranges of that nest level were calculated the method then iterated to the next (higher) level in the nest and performed the same function, this time only comparing the start pages for destination dicts on a nest level at or above the nest level of the dict in question.

```python
# Itterating through each nest level beinging with the deepest level:
for nest_lvl in reversed(unique_nest_vals):

  # Itterating through each dictionary in the list copy:

  for dict in self.destination_lst:
    # Defining the main dict's position in the list:
    dict_index = self.destination_lst.index(dict)

    # Using the nearest destination dict that is at the same list lvl or higher:
    if dict['Nested_level'] == nest_lvl:

      print('CURRENT DESTINATION:', dict['Title'], 'START PAGE:',
      dict['Start_Page'], 'NEST LEVEL:', dict['Nested_level'])


      # Itterating through each destiation dict AFTER the main dict in the list:
      for next_dict in self.destination_lst[dict_index+1:]:

        # Conditional only performs prange algo if there is another
        # destiation on the same or higher nest level. If not it formats manually:
        if self.destination_lst.index(next_dict) == self.destination_lst.index(self.destination_lst[-1]):

          # This means that this destination occurs for rest of pdf:
          dict['Page_Range'] = (dict['Start_Page'], self.getNumPages())

          print('ADJACENT DESTINATION:', dict['Title'],
          'START PAGE', dict['Start_Page'], 'NEST LEVEL:',
          dict['Nested_level'])

        else:
          # Only Assigns 'End_Page' variable if next_dict is on an equal or higher nest lvl:
          if next_dict['Nested_level'] <= nest_lvl:

            # Replacing Start_Page & End_Page dict items w/ page range tuple:
            dict['Page_Range'] = (dict['Start_Page'], next_dict['Start_Page'])
            del dict['Start_Page']

            print('ADJACENT DESTINATION:', next_dict['Title'],
            'START PAGE', next_dict['Start_Page'], 'NEST LEVEL:',
            next_dict['Nested_level'])

            break

          else:
            continue

          # Brute Force Conditional to catch Destination the ] Conditional algo missed:
          for dict in self.destination_lst:
              if 'Page_Range' in dict:
                  del dict['Start_Page']
                  pass

              else:
                dict['Page_Range'] = (dict['Start_Page'], self.getNumPages())
                del dict['Start_Page']
```

**NOTE: This method is REALLY INEFFICIENT and 10000% NEEDS to be replaced by a recursive method that performs the same function in a way that is more pythonic and more efficient**

## Text Extraction
Once the `self.destination_lst` has been fully constructed via the `pop_destination_lst() and build_toc()`
methods, the next step is to extract all the text data for each destination. This is done by calling the
`build_destination_text()` method. This method simply iterates over the destinations in `destination_lst` and uses the pdfplumber page and text extraction methods to create a new dictionary which contains a list of strings representing all the text extracted for each destination keyed by each destination title:

```python
# Iterating through list of destination dicts:
for dict in self.destination_lst:

  pdf_pages = self.pdf_plumb.pages[start_page:end_page]

  # Iterating through page objects to extract text into list:
  for page in pdf_pages:
    text = page.extract_text()
    text_page_lst.append(text)

  # Creating main dict:
  indexed_text_dict[dict['Title']] = text_page_lst
```
The end result of this, when called by the __init__ method is the variable `self.indexed_text_dict` that stores pdf textual data as follows:
```python
{'Title_of_pdf_section':[list of pdf test strings with each string being the text of a single page]}
```

## Search Method
The purpose of the search method `pdf.get_sections()` is to provide an API for querying the main pdf object for text from specific
sections of the pdf. It is done by a very straightforward conditional statement that compares input search `keywords` to the destination
dictionary keys and builds a dictionary containing only the key-value pairs that were found via the keyword search.

Keywords and dictionary keys are converted to lowercase in order to perform the search, making the search inputs case-insensitive.

Example of the section search functionality:
```python
XOM = pdf('tests/test_pdfs/ExxonMobil 2019 10-K Report.pdf')
XOM.get_sections('mine')

# Would Return:
# {'ITEM 4. MINE SAFETY DISCLOSURES': [list of strings]}
```
## Sqlite Database API
The `db_api.py` file contains the `pdf_db()` object that acts as an api for reading and writing the information generated from the `pdf_parser` methods:

### `pdf_db(db_path)`
To interact with the sqlite database that contains the pdf data the object must be initialized with a string that represents the path to the database. In initializing the `pdf_db` object the database file is created if it does not currently exist, instance variables such as connection and cursor objects are declared and a main logging table called `Summary` is created with the following Schema:
| Name | Ticker |Pdf_type| Date | Path | Date_added |
|------|--------|--------|------|------|------------|
| TEXT |  TEXT  |  TEXT  | TEXT | TEXT | TEXT       |

 This table will be used to provide information about the current database.

#### `pdf_to_db(self, pdf_path, table_name, pdf_type, pdf_date, ticker):`
This is the api that uses the `pdf_parser` object to convert a pdf into a series of key-value pairs as described above and write the associated data to the database. The method initializes a `pdf_parser` object by the `pdf_path` string. It then iterates through all the relevant data generated by this object and writes it to the sqlite database table defined by the Parameters `table_name` and `pdf_date` according to the following schema:
|Section|Start_Page|End_Page|Section_Text|Cosine_Similarity|Jaccard_Similarity|Minimum_Edit_Distance|Simple_Similarity|
|-------|----------|--------|------------|-----------------|------------------|---------------------|-----------------|
| TEXT  | INTEGER  |INTEGER | TEXT       | REAL            | REAL             |REAL                 |REAL             |

The Section_Text column is populated with the raw text extracted from a pdf section that undergoes a cleaning process to make the textual data easier to analyze. The raw text is transformed using the `pdf_db.clean_text()` and the `pdf_db.tokenize_text()` methods described below. The 'cleaned' output of these methods are what is written to the Section_Text column of the database:
```python
# Iterating through the pdf_parser indexed_text_dict and writing to db:
  for key in pdf_parser.indexed_text_dict:

      # Converting the list of strings associated with each dict key to single str:
      raw_txt = ' '.join(pdf_parser.indexed_text_dict[key])

      # Cleaning text into nlp friendly format:
      section_txt = pdf_db.clean_text(raw_txt)

      # Converting the text into a Lemmatized format for further nlp processing:
      section_txt = pdf_db.tokenize_text(section_txt)
```

The other data tables relating to similarity metrics such as `Cosine_Similarity` are not modified in this method. These similarity columns are populated in a later method `perform_sim_calculation()`. All similarity columns are populated with NULL values when created via this method.

The `pdf_to_db()` method also writes logging/meta-data about the earlier pdf table to the `Summary` table previously described.

Example:
```python
test = pdf_tb('test_db')
test.pdf_to_db('path_to_Exxon_pdf', 'Exxon_pdf_tbl_title', '10_K', '1/10/2019', "XOM")
```

#### `build_ticker_tbl(self, ticker)`
The method builds a table in the database that contains a list of all pdf tables (by their date and name) of a specific ticker symbol.

The table that is created by the method is as follows:

|Name|Pdf_type|Date|Cosine_Similarity|Jaccard_Similarity|Minimum_Edit_Distance|Simple_Similarity|
|----|--------|----|-----------------|------------------|---------------------|-----------------|
|TEXT| TEXT   |TEXT|REAL             |REAL              |REAL                 |REAL

Where `Name` is the name of a table in the database and `Date` and `Pdf_type` are the date and pdf category that are associated with the pdf of said table. The similarity columns are all populated with NULL values as these columns are populated and manipulated via the `perform_sim_calculation()`
method. Any description of these tables that does not include the similarity columns just assumes that they have not yet been populated via the `perform_sim_calculation()` method.

This data is extracted by querying the `Summary` table for a list of all rows where the `Ticker` value is equal to the `ticker` input parameter and then writes the `Name`, `Date` and `Pdf_type` values from this row into the `{Ticker}_tables` table that was generated by the method earlier.

Example:
```python
test = pdf_db('test_db')
test.build_ticker_tbl('XOM')
```

In example if the 'Summary' table in the database 'test_db' contains the following row:
|   Name   | Ticker |Pdf_type|   Date   | Path | Date_added |
|----------|--------|--------|----------|------|------------|
|'pdf_name'| 'XOM'  | '10_K' |'pdf_date'|'path'|'date_added'|

Then the `test.build_ticker_tbl('XOM')` method would create (or write to if it exists) a table called `XOM_tables` and writes the row to the table:
|   Name   |Pdf_type|   Date   |
|----------|--------|----------|
|'pdf_name'| '10_K' |'pdf_date'|

#### `perform_sim_calculation(self, ticker)`
This is the main method that calculates and writes the similarity metrics between relevant pdfs to each respective table. This method is not inherently complicated. It is however very complicated to describe effectively. The best way of describing how this method extracts the relevant pdf tables, sections and text as well as how it calculates the similarity metrics is via pseudocode and hastily made diagrams:

```python
# Using XOM as an example:
test = pdf_db(':test_db_path')
test.perform_sim_calculation('XOM')

# Extracts dataframe of all data from the table {ticker}_tables
tuple_lst = self.c.execute(f"SELECT * FROM {table_name}")

# Iterating through the list of row tuples and performing sim operations on the respective table:
for tuple in tuple_lst:

  # For each Table name determining the corresponding pdf table from the previous year:
  pervious_year_pdf = pdf_db.build_tbl_name_tuple(tuple, tuple_lst)

  # Extracting all sections from both pdf tables:
  init_pdf_sections = [self.c.execute('tbl_query')]
  second_pdf_sections = [self.c.execute('tbl_query')]

  # Creating a common list of section names between pdfs:
  common_sections = list(set(init_pdf_sections).intersection(second_pdf_sections))

  # Iterates through each section in section name to perform sim analysis:
  for section in common_sections:

    # Extracting text for each Section from both pdfs:
    init_pdf_section_txt = self.c.execute('query to Section_Text column of {previous_year_tuple[0]}')
    second_pdf_section_txt = self.c.execute('query to Section_Text column of {previous_year_tuple[1]}')

    # Calculating all similarity metrics between Section_text:
    cosine_sim = textdistance.cosine(init_pdf_section_text, second_pdf_section_text)
    jaccard_sim = textdistance.jaccard(init_pdf_txt_lst, second_pdf_txt_lst)

    # Writing similarity values to the inital pdf table:
    self.c.execute("Update Statement to {prev_yr_tbl[0]}")

  # After section similarity calculations, perform sim calculations on text content
  # of the entirety of both pdfs:

  # Extracting full text from both pdfs:
  init_pdf_full_txt = [' '.join(self.c.execute('Full text query to {previous_year_pdf[0]}'))]
  second_pdf_full_txt = [' '.join(self.c.execute('Full text query to {previous_year_pdf[1]}'))]

  # Calculating similarity metrics:
  pdf_cosine_sim = textdistance.cosine(init_pdf_full_txt, second_pdf_full_txt)
  pdf_jaccard_sim = textdistance.jaccard(init_pdf_full_txt, second_pdf_full_txt)

  # Writing sim data to the {ticker}_tables database table:
  self.c.execute('Update statement to {ticker}_tables')
```
This process is also crudely described in the following diagram:
![IMAGE NOT FOUND](placeholder)

From a functionality perspective the only thing that you really need to know about the `perform_sim_calculation()` method is that it populates the `{ticker}_tables` and all individual pdf tables of the same ticker with their similarity values. It calculates the similarly metrics between a pdf and its corresponding pdf of the previous year. For example if there is a 10-K report from 2019 it will perform a similarly comparison between it and the 10-K report from 2018.

Determining the the corresponding pdf of the previous year is done by the `build_tbl_name_tuple` method. All of the similarity calculations are done using the `textdistance` library for implementing nlp similarity algorithms. This may change in the future however as more custom implementations of nlp similarity algorithms become necessary. 

The correct sequence with which to call these methods when adding pdfs to the database is as follows:
```python
# Initializing datbase api object:
test = pdf_db('path_to_test_db')

# Inserting pdf's to database:
test.pdf_to_db('path to pdf ', 'Tesla_10_K_2018', '10_K', '01/08/20180', 'TSLA')
# etc etc etc

# Building the summary data table for all tables containing data about Tesla:
test.build_ticker_tbl('TSLA')

# Performing similarity calculations and writing all sim calculations to TSLA tables:
test.perform_sim_calculation('TSLA')
```

#### `get_table_data(self, table_name, section_title=None)`
This is the main query method that is used to extract data from the database. Once the `pdf_db` method is initialized/connected to the sqlite database it executes a SELECT * FROM query to the database. The table name specified by the method is the table from which data will be queried.

If no `section_title` is specified then the entire data table is queried and returned as a pandas dataframe using the `pd.read_sql_query()`. If a `section_title` is specified then the database table is searched and a dictionary containing the data from a single row of the table where the `Section` column value is equal to the `section_title` parameter is returned.

Example:
```python
test = pdf_db('path_to_test_db')
test.get_table_data('EXXON_10K', 'SIGNATURES')

# ---------OUTPUT-----------------------------
{'Title': 'SIGNATURES', 'Start_Page': 128, 'End_Page': 136, 'Section_Text': "EXAMPLE_TEXT"}
```

#### `clean_text(text)`
A basic method that uses list comprehension to format raw text strings into a format more efficient and friendly for natural language processing. The method performs the following data cleaning on the input string:
- Removes numerical data
- Removes any form of punctuation
- Removes any python native string formatting information (\n, \t, etc..)

Example:
```python
# Initializing database method and calling text cleaning method:
pdf_db('test_db').clean_text('''The method s2342342erves as a 'helper' method???? th////at modifies the raw text
 ex\t\ttracted fro23432m \nthe ..pdf......_parser 24234. It c!!!423423onverts the string into a more
 nlp f4234riendly form\nat. 324234It performs,..... 42323424234the following formatting:''')

#---------------------------OUTPUT---------------------------------#
"""The method serves as a helper method that modifies the raw text extracted from the pdfparser  It converts the string into a more nlp friendly format It performs the following formatting"""
```
#### `tokenize_text(text)`
A basic method that uses the nltk toolkit to tokenizes and lemmatize the input text. It should be noted that this is done by a constant/semi-redundant use of converting a large string into a list of words and back. This may cause performance issues if method is applied on very large datasets.

**Note:** The nltk library that is being used in both `tokenize_text()` and `clean_text()` need their own nltk word corpus. If these are not installed then these methods will not function. Simply insall them via the:
Example:
```python
import nltk
nltk.download('wordnet')
nltk.download('stopwords')

# Initializing the corpus:
stopwords = nltk.corpus.stopwords.words('english')
```

Example of `tokenize_text()`:
```python
example_txt = """A basic method that uses the nltk toolkit to tokenizes and lemmatize the input text. It should be noted that this is done by a constant/semi-redundant use of converting a large string into a list of words and  back. This may cause performance issues if method is applied on very large datasets."""

pdf_db.tokenize_text(example_txt)

#------------------Output------------------------#
"A basic method us nltk toolkit tokenizes lemmatize input text It noted done constant semi redundant use converting large string list word back This may cause performance issue method applied large datasets "

```

**Note:** It is unknown if this is the most effective way of accurately pre-processing pdf text data as it may be too reductive, especially when combined with the `clean_text()` method as is the case in the `pdf_to_db` method. If this is the case a more simplistic data cleaning process may be necessary.


#### `build_tbl_name_tuple(init_tuple, tuple_list)`
This is another helper method that is called in the main Database Writing Methods. It ingests a tuple of data extracted from a `Ticker_tables` table row in the format of (table_name, pdf_type, pdf_date) and a list of other tuples extracted from other table rows.

It then makes use of `datetime` methods and list comprehension to iterate through the list of tuples and extracts the tuple that corresponds to the pdf of the same type and previous year of the `init_tuple`. It then returns a tuple of the table names of the initial tuple and the extracted tuple in the format (init_tuple_name, extracted_tuple_name). If a tuple is not found during the list comprehension then the tuple returned is in the format of (init_tuple_name, None).

Example:
```python
initial_tuple = ('EXXON_10K_2019', '10_K', '31/12/2019')

tuple_list = [('EXXON_10K_2019', '10_K', '31/12/2019'), ('EXXON_10K_2018', '10_K', '31/12/2018'),
('EXXON_10K_2017', '10_K', '31/12/2017'), ('EXXON_10K_2016', '10_K', '31/12/2016'),
('EXXON_10K_2015', '10_K', '31/12/2015'), ('EXXON_10K_2018', '10_Q1', '31/12/2018')]


pdf_db.build_tbl_name_tuple(initial_tuple, tuple_list)

# <-----------------------Output----------------------------------------------->
('EXXON_10K_2019', 'EXXON_10K_2018')

# If tuple_list contains no matches:
tuple_list = [('EXXON_10K_2019', '10_K', '31/12/2019'), ('EXXON_10K_2017', '10_K', '31/12/2017'), ('EXXON_10K_2016', '10_K', '31/12/2016'), ('EXXON_10K_2015', '10_K', '31/12/2015'),
('EXXON_10K_2018', '10_Q1', '31/12/2018')]

pdf_db.build_tbl_name_tuple(initial_tuple, tuple_list)

# <-----------------------Output----------------------------------------------->
('EXXON_10K_2019', None)
```
