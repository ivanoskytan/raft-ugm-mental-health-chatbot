import logging
from .ocr_converter import OCRConverter
from .data_chunker import DataChunker
from .vector_indexer import VectorIndexer

class VectorStoreBuilder:
    def __init__(self):
        self.ocr_converter = OCRConverter()
        self.data_chunker = DataChunker()
        self.vector_indexer = VectorIndexer()

    def run(self):
        logging.info("-- Running OCR Conversion")
        self.ocr_converter.convert_all_pdfs()

        logging.info("-- Chunking Text Files")
        self.data_chunker.chunk_all_files()

        logging.info("-- Building Vector Index")
        self.vector_indexer.build_index()

        logging.info("-- Vector Store Building Process is completed")