# Importing PyPDF2 PDF management package:
import PyPDF2 as p2
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
    the initalization of object and heavily make use of the PyPDF2 library. It is
    a child object of the PyPDF2 PdfFileReader object as many of the methods
    used by said class are integral to the function of this object. This will
    primarily be used as a base class to be inherited for other packages and methods.

    Parameters
    -----------
    file_path : str
        The string representing the file path to the pdf.

    Methods
    -----------
    pop_destination_lst : # TODO: Write pop_destination_lst description.
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
        print(self.destination_lst)

        # Calling self.build_toc:
        self.build_toc(self.destination_lst)


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
        # TODO: Write method documentation after it is built.
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

        # Defining a copy of the self.destination_lst to manipulate:
        dest_lst_cpy = self.destination_lst

        # Defining new list to store all the newly modified destination dicts:
        orderd_destination_lst = []

        # Counter variable to dictate at what level of the nest the loop operates:
        nest_level = max(unique_nest_vals) # lowest level in nest is highest num.

        # Itterating through each level of the nest:
        for element in unique_nest_vals:

            # Itterating through the destiation list based on nest level:
            for dict in dest_lst_cpy:

                # Only itterates through elements at the specified nest level:
                if dict['Nested_level'] == nest_level:

                    # Tracking list position of dict:
                    dict_loc = dest_lst_cpy.index(dict)

                    # If dict is at lowest remaining nest level:
                    try:
                        End_Page = dest_lst_cpy[dict_loc + 1]['Start_Page']
                    except:
                        End_Page = self.getNumPages()
                        
                    dict['End_Page'] = End_Page

                    # Once dict is modified it is removed from dest_lst_cpy:
                    # Adding it to orderd_destination_lst:
                    orderd_destination_lst.append(dict)
                    dest_lst_cpy.remove(dict)


                    # TODO: Fix the issues with this selection module:
                    # Write it out on paper and complete the algorithm.

                    print(dest_lst_cpy)
                    print(orderd_destination_lst)
                    print(nest_level)

            # Changing nest_level to operate at a shallower nest level:
            nest_level = nest_level - 1


# Test:
pdf('tests/test_pdfs/ExxonMobil 2019 10-K Report.pdf')
