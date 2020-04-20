# PDF Ingestion and Data Transformation Package with PyPDF2 and pdfplumber
* Financial Report Ingestion Engine Structure
* Table of Contents Extraction

### Financial Report Ingestion
The ingestion of a firms 10-Q & 10-K PDF Reports is mainly done via the PyPDF2
library. This documentation, in addition to describing the workings of the ingestion
engine, will also supplement the PyPDF2 documentation.

The pdf_ingestion_engine is structured as a module designed to ingest a PDF via
a file path and transform said PDF into text data indexed by financial report
sections to be fed into the natural language processing package.  


### Table of Contents Extraction:
The first step to implementing the lazy prices algorithm is to extract the table
of contents from a financial statement.
