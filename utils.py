import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

os.makedirs("./KnowledgeBase", exist_ok=True)
os.makedirs("./models", exist_ok=True)

def get_embedding_model(model_dir = "models/all-MiniLM-L6-v2"):
    if os.path.exists(model_dir):
        print(" Loading existing embedding model from disk...")
        embedder = SentenceTransformer(model_dir)
    else:
        print(" Downloading embedding model...")
        embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        # Save the model locally for future use
        embedder.save(model_dir)
    return embedder


def get_knoweledge_base(kb_file="kb.json", index_file="faiss.index", emb_file="embeddings.npy"):
    
    kb_file = os.path.join("KnowledgeBase", kb_file)
    index_file = os.path.join("KnowledgeBase", index_file)
    emb_file = os.path.join("KnowledgeBase", emb_file)
    
    with open(kb_file, "r") as f:
        faqs = json.load(f)
    
    # Extract Q & A
    questions = [item["question"] for item in faqs]
    answers = [item["answer"] for item in faqs]

    # Load or create FAISS index
    if os.path.exists(index_file) and os.path.exists(emb_file):
        print(" Loading existing FAISS index + embeddings...")
        embeddings = np.load(emb_file)
        index = faiss.read_index(index_file)
    else:
        print("Creating new FAISS index...")
        embedder = get_embedding_model()
        embeddings = embedder.encode(questions, convert_to_numpy=True)
        d = embeddings.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(embeddings)

        faiss.write_index(index, index_file)
        np.save(emb_file, embeddings)
    return index, answers