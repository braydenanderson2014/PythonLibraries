#this classs will tak in a pdf/multiple pdf's and condense them into a basic understanding of the content
import os
from PyPDF2 import PdfReader, PdfWriter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import LLMChain
from langchain.schema import Document
from langchain.callbacks import get_openai_callback

class SimplifyAndCondense:
    def __init__(self):
        pass