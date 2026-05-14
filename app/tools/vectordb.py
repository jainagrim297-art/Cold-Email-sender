import chromadb

class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="company_docs")

    def add_document(self, doc_id, text, metadata):
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )