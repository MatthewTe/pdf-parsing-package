# Importing PDF management libraries:
import PyPDF2 as p2
import pdfplumber

# Importing data management packages:
from collections import Counter
# Importing native python package management libs:
import warnings


class pdf(p2.PdfFileReader):
    """
    pdf() object contains all the methods necessary to parse a pdf file and
    produce standardized outputs that can be fed into more complex analysis
    processes such as NLP.

    Critically most of the methods stored within this object are used to
    construct instance variables and as such many of the methods are called within
    the initalization of object and heavily make use of the PyPDF2 and pdfplumber
    libraries. It is a child object of the PyPDF2 PdfFileReader object as many
    of the methods used by said class are integral to the function of this object.
    This will primarily be used as a base class to be inherited for other packages and methods.

    Parameters
    -----------
    file_path : str
        The string representing the file path to the pdf.

    echo : bool
        echo determines if print statements describing methods processes are
        output to the console. By deafult echo=False

    Methods
    -----------
    pop_destination_lst : A recursive method used to parse the .getOutlines()
    object and produce dictionaries generated from Destination objects

    build_toc : The main method that compliles the Table of Contents of the pdf
    by modifying the main list of Destination dictionaries.

    build_destination_text :

    get_sections :
    """

    def __init__(self, file_path, echo=False):

        # Initalizing PdfFileReader child object:
        super().__init__(file_path)

        # instance echo variable
        self.echo = echo

        # File path:
        self.file_path = file_path

        # Conditional to decrypt pdf if encrypted:
        if self.isEncrypted == True:

            # Getting user to input a password:
            password = input('Pdf is encrypted, please input the decryption password: ')

            self.decrypt(password)

            # Defining pdf file object for pdfplumber with password:
            self.pdf_plumb = pdfplumber.open(file_path, password=password)

        # If pdf is not encrypted the pdf file object for pdfplumber is defined:
        else:
            self.pdf_plumb = pdfplumber.open(file_path)


        # Declaring the instance list varialble to be populated by .pop_destination_lst():
        self.destination_lst = []

        # Calling the pop_destination_lst() method to populate the self.pop_destination_lst:
        self.pop_destination_lst(self.getOutlines(), counter=0)
        #print(self.destination_lst)

        # Calculating the Page ranges for each destiation:
        self.build_toc()

        # Using pdf_plumb library to extract tables and text, indexing them by section:
        self.indexed_text_dict = self.build_destination_text()


    def pop_destination_lst(self, dest_obj, counter):
        '''
        A recursive method used to parse the .getOutlines() object and produce
        dictionaries generated from Destination objects. These dicts are then
        written to an instance list to be further parsed by additional methods.

        Parameters
        ----------
        dest_obj : PyPDF2.getOutlines() Object
            A method from PyPDF2 that returns a nested series of PyPDF2
            Destination() objects extracted from the PDF.

        counter : int
            A counter 'dummy' variable used in building the toc dicts. Itterates
            ever time a recursion takes place. Used to keep track of what level
            each dict is in the nest.
        '''


        if type(dest_obj) is not list:

            # Creating a new dict with only necessary variables:
            dest_dict = {'Nested_level': counter, 'Title': dest_obj.title,
            'Start_Page': self.getDestinationPageNumber(dest_obj)}

            # Adding new dict to the destiation list instance variable:
            self.destination_lst.append(dest_dict)
            #print(dest_dict)

        else:
            for x in dest_obj:
                # Itterating the counter to indicate the nested level:
                self.pop_destination_lst(x, counter+1)

    def build_toc(self):
        '''
        The main method that compliles the Table of Contents of the pdf. It first
        modifies the list of PyPDF destiation dictionaries to inclue the page
        range of each destiation. This is done with a simple nested page range
        detection algorithm which is described in depth in the documenation.

        The method does not return an object, it modifies the existing dictionaries
        in the self.destination_lst instance list.
        '''

        # Declearing list to store counts for each destiation's nest level:
        nest_lvl_lst = []

        # Itterating over the destination_lst to build the count list:
        for dict in self.destination_lst:
            nest_lvl_lst.append(dict['Nested_level'])

        # Creating set to extract a list containing the unique nest lvl values:
        unique_nest_vals = list(set(nest_lvl_lst))

        # Counting the nests for each nest level from the nest level list:
        nest_lvl_count = Counter(nest_lvl_lst)

        # Parsing the nest_lvl_lst to select the lowest int i.e. highest level in nest:
        highest_nest_lvl = min(nest_lvl_lst)

        # Creating a list of all Destinations at the highest nest level:
        highest_nest_lst = []
        for dict in self.destination_lst:

            # Checking each destiation dict for its nest level:
            if dict['Nested_level'] == highest_nest_lvl:
                highest_nest_lst.append(dict)

        #print(highest_nest_lst)

        #print(self.getNumPages())

        #print(reversed(unique_nest_vals))


        if self.echo is True:
            '# Itterating through Destinations to determine their page ranges: '
            # Print Statements are for diagnositics & comprehension during run:
            print('-------------------------------------------------------------')
            print('| PDF SECTION-PAGE-RANGE-DETECTION ALGORITHM RESULTS        |')
            print('-------------------------------------------------------------')

        # Itterating through each nest level beinging with the deepest level:
        for nest_lvl in reversed(unique_nest_vals):

            # Itterating through each dictionary in the list copy:
            for dict in self.destination_lst:

                # Defining the main dict's position in the list:
                dict_index = self.destination_lst.index(dict)

                # Using the nearest destination dict that is at the same list lvl or higher:
                if dict['Nested_level'] == nest_lvl:

                    if self.echo is True:
                        print('CURRENT DESTINATION:', dict['Title'], 'START PAGE:',
                        dict['Start_Page'], 'NEST LEVEL:', dict['Nested_level'])


                    # Itterating through each destiation dict AFTER the main dict in the list:
                    for next_dict in self.destination_lst[dict_index+1:]:

                        # Conditional only performs prange algo if there is another
                        # destiation on the same or higher nest level. If not it formats manually:
                        if self.destination_lst.index(next_dict) == self.destination_lst.index(self.destination_lst[-1]):

                            # This means that this destination occurs for rest of pdf:
                            dict['Page_Range'] = (dict['Start_Page'], self.getNumPages())

                            if self.echo is True:
                                print('ADJACENT DESTINATION:', dict['Title'],
                                'START PAGE', dict['Start_Page'], 'NEST LEVEL:',
                                dict['Nested_level'])

                        else:

                            # Only Assigns 'End_Page' variable if next_dict is on an equal or higher nest lvl:
                            if next_dict['Nested_level'] <= nest_lvl:

                                # Replacing Start_Page & End_Page dict items w/ page range tuple:
                                dict['Page_Range'] = (dict['Start_Page'], next_dict['Start_Page'])

                                if self.echo is True:
                                    print('ADJACENT DESTINATION:', next_dict['Title'],
                                    'START PAGE', next_dict['Start_Page'], 'NEST LEVEL:',
                                    next_dict['Nested_level'])

                                break

                            else:
                                continue

                    if self.echo is True:
                        print(dict)
                        print('-------------------------------------------------------------')

        # Brute Force Conditional to catch Destination the shitty Conditional algo missed:
        for dict in self.destination_lst:

            if 'Page_Range' in dict:
                del dict['Start_Page']
                pass

            else:

                dict['Page_Range'] = (dict['Start_Page'], self.getNumPages())
                del dict['Start_Page']

                runtime_warn_msg = f'''The "{dict['Title']}" section was not caught by the
                page-range-detection-algorithm. It was manually modified as such:

                ----------------------------------------------------------------
                {dict}
                ----------------------------------------------------------------

                The page range of this section may be incorrect.
                '''

                warnings.warn(runtime_warn_msg, category=RuntimeWarning)

    def build_destination_text(self):
        '''
        Method iterates through the instance list destination_lst and uses the
        pdf_plumb library to extract all the text and tables from each individual
        destiation section and creates a dictionary where the keys is the title
        of the destination from which the text data was extracted.

        Returns
        -------
        indexed_text_dict : dict
            A dictionary storing all the text and table-extracted-text from the
            pdf indexed by destiation titles.
        '''


        # Main dictionary:
        indexed_text_dict = {}

        # Iterating through destination_lst extracting all relevant textual data:
        for dict in self.destination_lst:

            # list of all page strings:
            text_page_lst = []

            # Unpacking variables from dict page range tuple:
            (start_page, end_page) = dict['Page_Range']

            # Initalzing the list of pdfplumber page objects given the page range:
            pdf_pages = self.pdf_plumb.pages[start_page:end_page]

            # Iterating through list of pdf pages and extracting text strings:
            for page in pdf_pages:

                # Building text_page_lst:
                text = page.extract_text()

                text_page_lst.append(text)

            indexed_text_dict[dict['Title']] = text_page_lst

        return indexed_text_dict

    def get_sections(self, *keywords):
        '''
        .get_sections method parses the instance dictionary containing all
        extracted pdf text and returns the text contained in pdf sections
        based on the input *keywords. This method gives the pdf() object its main
        search functionality.

        Parameters
        ----------
        *keywords : *arg string
            The key word strings that will be used by the method to perform a search
            of the self.indexed_text_dict keys.

        Returns
        -------
        search_results : dict
            A dictionary containing all the elements of self.indexed_text_dict
            that were selected by this search method.
        '''
        # Empty main dict:
        search_results = {}

        # Iterating through indexed_text_dict keys to perform search:
        for key in self.indexed_text_dict.keys():

            #print(key.lower())

            # Comparing each key to every seach keyword:
            for keyword in keywords:

                # Appending key-value pair from self.indexed_text_dict if search selects it:
                if keyword.lower() in key.lower() and key not in search_results:

                    search_results[key] = self.indexed_text_dict[key]

                else:
                    continue

        return search_results






# Test:
XOM = pdf('tests/test_pdfs/ExxonMobil 2019 10-K Report.pdf')
print(XOM.get_sections('mine'))
