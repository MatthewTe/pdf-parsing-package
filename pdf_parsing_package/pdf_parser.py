# Importing PDF management libraries:
import PyPDF2 as p2
import pdfplumber

# Importing data management packages:
from collections import Counter

# Creating class that is meant to represent the Financial Report PDF:
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

    Methods
    -----------
    pop_destination_lst : A recursive method used to parse the .getOutlines()
    object and produce dictionaries generated from Destination objects

    build_toc : The main method that compliles the Table of Contents of the pdf
    by modifying the main list of Destination dictionaries.
    """

    def __init__(self, file_path):

        # Initalizing PdfFileReader child object:
        super().__init__(file_path)

        # File path:
        self.file_path = file_path

        # Conditional to decrypt pdf if encrypted:
        if self.isEncrypted == True:

            # Getting user to input a password:
            password = input('Pdf is encrypted, please input the decryption password: ')

            self.decrypt(password)

        # If pdf is not encrypted the conditional is passed over:
        else:
            pass


        # Declaring the instance list varialble to be populated by .pop_destination_lst():
        self.destination_lst = []

        # Calling the pop_destination_lst() method to populate the self.pop_destination_lst:
        self.pop_destination_lst(self.getOutlines(), counter=0)
        #print(self.destination_lst)

        # Calling self.build_toc:
        #self.build_toc(self.destination_lst)



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

    def build_toc(self, destination_lst):
        '''
        The main method that compliles the Table of Contents of the pdf. It first
        modifies the list of PyPDF destiation dictionaries to inclue the page
        range of each destiation. This is done with a simple nested page range
        detection algorithm which is described in depth in the documenation.

        The method does not return an object, it modifies the existing dictionaries
        in the self.destination_lst list.


        Parameters
        ----------
        destination_lst : lst
            A list containing all the destination dictionaries extacted from the
            pdf via the self.pop_destination_lst() method.
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

                # Using the nearest destination dict that is at the same list lvl or higer:
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
                            #del dict['Start_Page']

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


                    print(dict)
                    print('-------------------------------------------------------------')

        # TODO: Integrate pdfplumber to get text data for each page range and index it.
        # TODO: Create the selection algo that determines appropriate nest level.



# Test:
pdf('tests/test_pdfs/ExxonMobil 2019 10-K Report.pdf')
