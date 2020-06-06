# Importing data management packages:
from datetime import datetime
import pandas as pd
# Importing the pdf api:
from pdf_parser import pdf
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

        # Creating a summary table if it does not exist:
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS Summary (
                    Name TEXT Primary Key,
                    Date TEXT NOT NULL,
                    Path TEXT NOT NULL UNIQUE,
                    Date_added TEXT NOT NULL)"""
                    )

        # Commiting cursor command to database:
        self.con.commit()

    # Method that writes a single pdf to the database:
    def pdf_to_db(self, pdf_path, table_name, pdf_date):
        '''
        The method makes use of the pdf_parser api to write the generated key-value
        dict to the sqlite dictionary.

        Parameters
        ----------
        pdf_path : str
            A string representing the path to the pdf file that will be initalized.

        table_name : str
            A string that represents the title of the sqlite database that the data
            will be read into.

        pdf_date : str
            A string that indicates the date relevant to the pdf being uploaded
            to the database. This string is also used to build the table name for
            the current pdf.
        '''
        # Building table title string:
        tbl_title = f"{table_name}_{pdf_date}"

        # Creating the table:
        self.c.execute(
            f"""CREATE TABLE {tbl_title} (
                Section TEXT Primary Key,
                Start_Page INTEGER,
                End_Page INTEGER,
                Section_Text TEXT)"""
                    )

        # Initalzing the pdf parsing object:
        pdf_parser = pdf(pdf_path)

        # Iterating through the pdf_parser indexed_text_dict and writing to db:
        for key in pdf_parser.indexed_text_dict:

            # Converting the list of strings associated with each dict key to single str:
            section_txt = ' '.join(pdf_parser.indexed_text_dict[key])

            # Iterating through the list of info_dicts of pdf sections for page range:
            for info_dict in pdf_parser.destination_lst:

                # If the info dict is for the section indicated by key, unpacking page range:
                if info_dict['Title'] == key:

                    # Unpacking tuple of page range:
                    (start_page, end_page) = info_dict['Page_Range']

            # Inserting each element of the indexed pdf content to table:
            self.c.execute(
                f"""
                INSERT INTO {tbl_title} VALUES (:section_name, :start_page,
                :end_page, :section_txt)""",
                {'section_name':key, 'section_txt': section_txt,
                 'start_page': start_page, 'end_page': end_page}
                    )

        # Building variables to be written to the Summary logging table:
        date_written = datetime.date(datetime.now())

        # Writing the logging/summary data to the summary database table:
        self.c.execute(
            """INSERT INTO Summary VALUES (:name, :date, :path, :date_written)""",
                {'name': tbl_title, 'date': pdf_date, 'path': pdf_path,
                'date_written': date_written}
                )


        # Commiting all changes to database:
        self.con.commit()

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
