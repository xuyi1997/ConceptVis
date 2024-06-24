import spacy
import pytextrank
import utils as utils
import os

class TextRankExtractor:

    def __init__(self, content = '', topic_num = 20):
        self.content = content
        self.topic_num = topic_num

    def process(self):
        # load a spaCy model, depending on language, scale, etc.
        nlp = spacy.load("en_core_web_sm")
        # add PyTextRank to the spaCy pipeline
        nlp.add_pipe("textrank")
        doc = nlp(self.content)
        count = min(self.topic_num, len(doc._.phrases))
        return [phrase.text for phrase in doc._.phrases[:count]]


if __name__ == "__main__":
    
    filename = 'C:\Repo\ConceptVisDemo\save\AItext.txt'
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist.")
        exit(1)

    raw_doc = utils.load_document(document_name=filename)

    extractor = TextRankExtractor(raw_doc)
    ret = extractor.process()
    print(ret)