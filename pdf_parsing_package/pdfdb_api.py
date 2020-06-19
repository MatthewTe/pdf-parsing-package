# Importing data management packages:
from datetime import datetime
import pandas as pd

# Importing textual data cleaning packages:
import string
import re

# Importing natural language packages:
import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textdistance
from difflib import Differ, SequenceMatcher
# nltk.download('wordnet')
# nltk.download('stopwords')

# Importing the pdf api:
from . import pdf_parser as pparser # For Production
# import pdf_parser as pparser # For Development

# Importing database libraries:
import sqlite3

# Class that represents the sqlite3 pdf db and its api:
class pdf_db(object):
    """
    An object that represents the sqlite database for the nlp pdf project.

    The pdf_db object contains all the methods and api's necessary to maintain
    and query the pdf sqlite3 database.

    Parameters
    ----------
    db_path : str
        This is a string that represents the path to the database. This string is
        either used to establish a connection with the database or to specify the
        location where the database will be created.
    """
    def __init__(self, db_path):
        # Creating the database or Creating a connection to the database:

        self.con = sqlite3.connect(db_path)

        # Creating a singular cursor to interact with the database:
        self.c = self.con.cursor()

        # Ensuring that the sqlite3 database supports foreign keys:
        self.c.execute("PRAGMA foreign_keys")

        # Enabling foreign key support if it is disabled:
        if self.c.fetchall()[0][0] == 0:

            self.c.execute("PRAGMA foreign_keys = ON")

        # Creating a summary table if it does not exist:
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS Summary (
                    Name TEXT Primary Key,
                    Ticker TEXT,
                    Pdf_type TEXT,
                    Date TEXT NOT NULL,
                    Path TEXT NOT NULL UNIQUE,
                    Date_added TEXT NOT NULL)"""
                    )

        # Commiting cursor command to database:
        self.con.commit()

# <-----------------------------Database Writing Methods------------------------>
    # Method that writes a single pdf to the database:
    def pdf_to_db(self, pdf_path, table_name, pdf_type, pdf_date, ticker):
        '''
        The method makes use of the pdf_parser api to write the generated key-value
        dict to the sqlite dictionary with the extracted strings cleaned for nlp
        processing by the .clean_text() and .tokenize_text() methods.

        Parameters
        ----------
        pdf_path : str
            A string representing the path to the pdf file that will be initalized.

        table_name : str
            A string that represents the title of the sqlite database that the data
            will be read into.

        pdf_type : str
            A string representing the category that the pdf is a part of. Eg: "10_K".

        pdf_date : str
            A string that indicates the date relevant to the pdf being uploaded
            to the database. This MUST be a full date in the form of dd/mm/yyyy.

        ticker : str
            A string that represents the ticker symbol associated with the pdf being
            read to the database. This ticker will be written to the Summary table.
        '''
        # Creating the table:

        self.c.execute(
            f"""CREATE TABLE IF NOT EXISTS {table_name} (
                Section TEXT Primary Key,
                Start_Page INTEGER,
                End_Page INTEGER,
                Section_Text TEXT,
                Cosine_Similarity REAL,
                Jaccard_Similarity REAL,
                Minimum_Edit_Distance REAL,
                Simple_Similarity REAL
                )"""
                    )

        # Initalzing the pdf parsing object:
        pdf_parser = pparser.pdf(pdf_path)

        # Iterating through the pdf_parser indexed_text_dict and writing to db:
        for key in pdf_parser.indexed_text_dict:

            # Try Catch if the pdf parser cannot extract text for a section:
            try:
                # Converting the list of strings associated with each dict key to single str:
                raw_txt = ' '.join(pdf_parser.indexed_text_dict[key])

                # Cleaning text into nlp friendly format:
                section_txt = pdf_db.clean_text(raw_txt)

                # Converting the text into a Lemmatized format for further nlp processing:
                section_txt = pdf_db.tokenize_text(section_txt)
                #print(section_txt)

                # Iterating through the list of info_dicts of pdf sections for page range:
                for info_dict in pdf_parser.destination_lst:

                    # If the info dict is for the section indicated by key, unpacking page range:
                    if info_dict['Title'] == key:

                        # Unpacking tuple of page range:
                        (start_page, end_page) = info_dict['Page_Range']

                # Inserting each element of the indexed pdf content to table:
                self.c.execute(
                    f"""
                    INSERT INTO {table_name} VALUES (:section_name, :start_page,
                    :end_page, :section_txt)""",
                    {'section_name':key, 'section_txt': section_txt,
                     'start_page': start_page, 'end_page': end_page}
                        )

            except:
                pass

        # Building variables to be written to the Summary logging table:
        date_written = datetime.date(datetime.now())

        # Writing the logging/summary data to the summary database table:
        self.c.execute(
            """INSERT INTO Summary VALUES (:name, :ticker, :pdf_type, :date, :path, :date_written)""",
                {'name': table_name, 'ticker': ticker, 'pdf_type':pdf_type,
                 'date': pdf_date, 'path': pdf_path, 'date_written': date_written}
                )

        # Commiting all changes to database:
        self.con.commit()

    # Method that creates a table containing all the summary data for a specific ticker:
    def build_ticker_tbl(self, ticker):
        '''
        This method creates and populates a table in the database that contains
        the table names and relevant information for a ticker symbol.

        Parameters
        ----------
        ticker : str
            A string representing the ticker symbol of the table that will be
            created and populated.
        '''
        # Building custom table name:
        table_name = f'{ticker}_tables'

        # Creating a database table for the ticker where all data will be written to:
        self.c.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                Table_name TEXT UNIQUE,
                Pdf_type TEXT,
                Date TEXT UNIQUE,
                Cosine_Similarity REAL,
                Jaccard_Similarity REAL,
                Minimum_Edit_Distance REAL,
                Simple_Similarity REAL
                FOREIGN KEY (Table_name) REFERENCES Summary (Name)
                )""")


        self.con.commit()

        # Executing a query to extract data from the Summary table for ticker data:
        self.c.execute(
            'SELECT * FROM Summary WHERE Ticker=:ticker_symbol',
            {'ticker_symbol':ticker})

        # Iterating through the self.c.fetchall() and writing data to ticker table:
        for tuple in self.c.fetchall():

            # Unpacking tuple:
            (tbl_name, ticker_symbol, pdf_type, pdf_date, pdf_path, date_uploaded) = tuple

            # Writing each row to the ticker database:
            self.c.execute(
                f"""
                INSERT OR IGNORE INTO {table_name} VALUES (:tbl_name, :pdf_type, :pdf_date)
                """, {'tbl_name': tbl_name, 'pdf_type':pdf_type, 'pdf_date':pdf_date})

        self.con.commit()

    # Method that executes natural language processing on all elements of a single ticker:
    def perform_sim_calculation(self, ticker):
        """
        Method performs all elements of nlp similarity calculations between all
        pdfs of a ceratin ticker symbol according to the lazy prices algorithm
        described by the Documentation.

        Parameters
        ----------
        ticker : str
            A string that represents the ticker of pdfs that the method performs
            similarity calculations on.
        """
        # Creating the main table name:
        table_name = f'{ticker}_tables'

        # Selecting the table based on the ticker symbol:
        self.c.execute(f"SELECT * FROM {table_name}")
        tuple_lst = self.c.fetchall()

        # Iterating through the list of row tuples and performing sim operations on the respective table:
        for tuple in tuple_lst:

            # Attempting to extract previous year table name from fetchall:
            prev_yr_tbl = pdf_db.build_tbl_name_tuple(tuple, tuple_lst)


            # If there is a previous year continue else pass:
            if prev_yr_tbl[1] != None:


                # Building a list of Sections from primary pdf using list comprehension:
                init_pdf_sections = [
                    section_name[0] for section_name in self.c.execute(
                    f"SELECT Section from {prev_yr_tbl[0]}")
                    ]

                # Builing a list of Sections form second pdf using list comprehension:
                second_pdf_sections = [
                section_name[0] for section_name in self.c.execute(
                f"SELECT Section from {prev_yr_tbl[1]}")
                ]

                # Creating a list of only common pdf section names in init and second lst:
                common_sections = list(set(init_pdf_sections).intersection(second_pdf_sections))

                # print(prev_yr_tbl[0], len(init_pdf_sections), init_pdf_sections)
                # print(prev_yr_tbl[1], len(second_pdf_sections), second_pdf_sections)
                # print(prev_yr_tbl[0], len(common_sections), common_sections)
                # print("-----------------------------------------------------------")

                # Iterating through the common_sections, comparing corresponding text:
                for section_name in common_sections:

                    # Extracting all text data from the section of inital pdf:
                    self.c.execute(
                        f"""SELECT Section_Text FROM {prev_yr_tbl[0]}
                        WHERE Section=:section_name""", {'section_name':section_name}
                        )

                    # self.c.fetchall() returns [(section_text, )]
                    init_pdf_section_text = self.c.fetchall()[0][0]

                    # Extracting all text data from the section of the second pdf:
                    self.c.execute(
                        f"""SELECT Section_Text from {prev_yr_tbl[1]} WHERE
                        Section = :section_name""", {'section_name':section_name}
                    )

                    # Unpacking fetchall in same format as above:
                    second_pdf_section_text = self.c.fetchall()[0][0]

                    # Calculating the similarity between the init and second text:
                    try: # If there are two strings available for calculations:

                        # Converting both text strings into word lists:
                        init_pdf_txt_lst = init_pdf_section_text.split()
                        second_pdf_txt_lst = second_pdf_section_text.split()

                        # Calculating cosine similarity:
                        cosine_sim = textdistance.cosine(init_pdf_section_text, second_pdf_section_text)

                        # Performing Jaccard Similarity calculation:
                        jaccard_sim = textdistance.jaccard(init_pdf_txt_lst, second_pdf_txt_lst)

                        # Performing Minimum edit distance or levenshtein distance calculation:
                        min_edit_dist = pdf_db.calc_minedit_dist(init_pdf_txt_lst, second_pdf_txt_lst)

                        # Writing similarity valus to the inital pdf table:
                        self.c.execute(
                            f"""UPDATE {prev_yr_tbl[0]}
                            SET Cosine_Similarity =:cosine_sim, Jaccard_Similarity =:jaccard_sim,
                            Minimum_Edit_Distance =:min_edit_dist
                            WHERE Section=:section_name""",
                            {'cosine_sim':round(cosine_sim, 3),
                            'jaccard_sim': round(jaccard_sim,3),
                            'min_edit_dist': min_edit_dist,
                            'section_name':section_name})

                    except:
                        pass

                # Executing Queries to extract list of ALL strings from each pdf:
                init_pdf_full_txt = ' '.join([
                    str_tuple[0] for str_tuple in self.c.execute(
                        f"SELECT Section_Text from {prev_yr_tbl[0]}")])

                second_pdf_full_txt = ' '.join([
                    str_tuple[0] for str_tuple in self.c.execute(
                        f"SELECT Section_Text from {prev_yr_tbl[1]}")])

                # Calculating cosine similarity between init and second pdf:
                pdf_cosine_sim = textdistance.cosine(init_pdf_full_txt, second_pdf_full_txt)

                # Converting full strings back into lists of strings:
                init_pdf_full_txt = init_pdf_full_txt.split()
                second_pdf_full_txt = second_pdf_full_txt.split()

                # Calculating the jaccard similarity between init and second pdf:
                pdf_jaccard_sim = textdistance.jaccard(init_pdf_full_txt, second_pdf_full_txt)

                # Calculating the Minimum Edit Distance between init and second pdf:
                min_edit_dist = pdf_db.calc_minedit_dist(init_pdf_full_txt, second_pdf_full_txt)

                # Writing full pdf similarity metrics to the {ticker}_tables data tables:
                self.c.execute(
                    f"""UPDATE {table_name} SET
                    Cosine_Similarity=:pdf_cosine_sim,
                    Jaccard_Similarity=:pdf_jaccard_sim,
                    Minimum_Edit_Distance=:min_edit_dist
                    WHERE Table_name=:pdf_table_name""",
                    {'pdf_cosine_sim':round(pdf_cosine_sim, 3),
                    'pdf_jaccard_sim':round(pdf_jaccard_sim, 3),
                    'min_edit_dist':round(min_edit_dist, 3),
                    'pdf_table_name':prev_yr_tbl[0]})

                self.con.commit()

            else:
                pass

# <------------------------------Query Methods---------------------------------->
    # Method that extracts an entire table of data:
    def get_table_data(self, table_name, section_title=None):
        '''
        A Method that uses the SELECT FROM table sql query to extract all the
        data from table in the database and representing it as a dataframe. It
        also allows the database query to be for a specific section title. If that
        is the case it only returns a dict containing this information.

        Parameters
        ----------
        table_name : str
            A string that will use to represent the name of the sql table that
            the data is being queried from. This string must match the name of
            the table being queried.

        section_title : str
            A string that represents the title of a pdf section to be extracted.
            By default this variable is None and if not specified then the bulk
            dataframe query is executed.

        Returns
        -------
        pdf_df :
            A dataframe that represents the table being extracted from the database.
            The pandas dataframe is built using the pd.read_sql_query() method
            to dynamically build a dataframe.

        OR

        pdf_dict : dict
            A dictionary containing the key value pairs of data that are returned
            for a specfic query using the input parameter section_title. The key
            values of the dict are {Title, Start_Page, End_Page, Text}
        '''
        # Conditional determining if a bulk query or a specific query runs:
        if section_title is None:

            # Creating df from sql table:
            pdf_df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.con)

            pdf_df.set_index(pdf_df.columns[0], inplace=True)

            return pdf_df

        else:

            # Custom query string:
            self.c.execute(
                f"SELECT * FROM {table_name} WHERE Section = :section_title",
                {"section_title": section_title}
                )

            # Building and returning dict of the tuple being extracted from fetchall:
            data = self.c.fetchall()[0]

            pdf_dict = {'Title': data[0], 'Start_Page': data[1],
            'End_Page': data[2], 'Section_Text': data[3]}

            return pdf_dict


# <---------------------------'Helper' Methods----------------------------------->
    # Method that cleans the raw text string generated by the pdf_parser object:
    def clean_text(text):
        '''
        The method serves as a 'helper' method that modifies the raw text
        extracted from the pdf_parser method. It converts the string into a more
        nlp friendly format. It performs the following formatting:

        - Removing punctuation.
        - Removing numbers
        - Removing python string formatting (/n, etc).

        Parameters
        ----------
        text : str
            A string of raw text generated from the pdf_parser method.

        Returns
        -------
        clean_text : str
            The input text string with the formatting described above applied.
        '''
        # Removing all punctuation, nums and special chars from main text w/ list comprehension:
        txt_lst = [words for words in text if words not in string.punctuation
            and words not in string.digits and words if ord(words)<126 and ord(words)>31]

        # Re-converting list back to single string:
        clean_text = ''.join(txt_lst)

        return clean_text

    # Method that tokenizes and pre-processes string data when being extracted:
    def tokenize_text(text):
        '''
        This method is meant to be used as another 'helper' method in the
        get_table_data() method. It converts the Section_text string stored in the
        database to a list of tokenized and Lemmatized strings, ready for NLP
        analysis.

        text : str
            A string representing all of the pre-processed textual data stored
            in the database table

        processed_txt : str
            A string built from the list of now processed strings via the .join
            method. This string is simplty the processed_txt_lst concatinated.
        '''
        # Splitting the text into a list of strings:
        str_lst = re.split('\W+', text)

        # Removing stopwords from str_lst:
        stopwords = nltk.corpus.stopwords.words('english')
        stp_wrds_rm = [word for word in str_lst if word not in stopwords]

        # Declaring Lemmatizer object and lemmatizing the word list:
        lemmatizer = WordNetLemmatizer()
        processed_txt_lst = [lemmatizer.lemmatize(word) for word in stp_wrds_rm]

        # Re-converting list of strings into single string for ease of db storage:
        processed_txt = ' '.join(processed_txt_lst)

        return processed_txt

    # Method that returns a tuple of a pdf table name and the pdf table name from
    # the previous year given an input tuple and a list of tuples returned from ticker_tables:
    def build_tbl_name_tuple(init_tuple, tuple_list):
        '''
        Method that iterates through a list of tuples of ('table_title', 'pdf_type', 'date')
        given an inital tuple of the same format and determines the tuple that
        corresponds to the previous year of the 'date' value of the init_tuple.

        See Docs for a more understandable explanation.

        Parameters
        ----------
        init_tuple : tuple
            A tuple extracted from a sqlite table query fetchall() list in the
            format ('table_title','pdf_type','date').

        tuple_list : lst
            A list of tuples in the format ('table_title','pdf_type','date'). This
            list is the list returned from the .fetchall() cursor method.

        Returns
        -------
        name_tuple : tuple
            A tuple in the format (init_tuple, previous_year_tuple) that is built
            by the method. It contains the intial tuple and the tuple from the list
            of tuples that is from the previous year and the same pdf category.
        '''
        # Unpacking init tuples:
        (table_title, pdf_type, pdf_date, cosine_sim, jaccard_sim,
            min_edit_dist, simple_sim) = init_tuple

        # Converting the pdf date to a datetime object:
        pdf_date = datetime.strptime(pdf_date, '%d/%m/%Y').date()

        # Creating a list of tuples where the date values is the pervious year and same pdf_type
        # via list comprehension: prev_tuple_lst SHOULD only contain one element.
        prev_tuple_lst = [

            # Converting 3rd element of tuple to a formatted datetime object:
            (element[0], element[1], datetime.strptime(element[2], '%d/%m/%Y').date())
            for element in tuple_list

            # Only extracting tuple list where 3rd element date is previous year of pdf_date:
            if datetime.strptime(element[2], '%d/%m/%Y').date().year == pdf_date.year - 1

            # And the pdf_type (2nd element) is equal to the pdf_type of the pdf_type variable:
            and element[1] == pdf_type
            ]

        # Building name_tuple out of the table names of the two relevant tuples:
        try:
            name_tuple = (table_title, prev_tuple_lst[0][0])

        except:
            # If no tuple is extracted via list comprehension, name_tuple[1] == None:
            name_tuple = (table_title, None)

        return name_tuple

    # Method calculates and returns the Minimum_Edit_Distance between two string lists:
    def calc_minedit_dist(string_1, string_2):
        '''
        Method that calculates the Minimum Edit Distance between two lists of strings
        via the use of the difflib package by tracking the changes necessary to
        transform string_1 list into string_2 list. It mainly makes use of the
        SequenceMatcher() method.

        Parameters
        ----------
        string_1 : lst
            The first list of string to be compared.

        string_2 : lst
            The second list of string to be compared.

        Returns
        -------
        num_edits : int
            An integer that represents the number of edits required to transform
            the string_1 list into the string_2 list.
        '''
        # Converting all strings in each list to lowercase:
        str_1_lower = [string.lower() for string in string_1]
        str_2_lower = [string.lower() for string in string_2]

        # Initalizing the SequenceMatcher object w strings lists:
        s = SequenceMatcher(None, str_1_lower, str_2_lower)

        # Creating the variable representing the number of edits performed during transformation:
        num_edits = 0

        # Iterating through SequenceMatcher() transformation tuple list:
        for tag, i_1, i_2, j_1, j_2 in s.get_opcodes():

            # If a replace action is performed:
            if tag == 'replace':

                # Increase by the highest value between (i_2 - i_1, j_2 - j_1):
                num_edits += max(i_2-i_1, j_2-j_1)

            # If a insert action is performed:
            elif tag == 'insert':

                # Increase by the difference between j_2 and j_1:
                num_edits += (j_2 - j_1)

            # If a delete action is performed:
            elif tag == 'delete':

                # Increase by the difference between i_2 and i_1:
                num_edits += (i_2 - i_1)

        return num_edits
