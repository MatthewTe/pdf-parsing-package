# PDF Ingestion and Data Transformation Package with PyPDF2 and pdfplumber
* Table of Contents Extraction
* Text Extraction

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
self.indexed_text_dict = {'Title_of_pdf_section':[list of pfd test strings with each string being the text of a sigle page]} 
```
