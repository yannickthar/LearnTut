import re
from sentence_transformers import SentenceTransformer, util
import torch


modell = SentenceTransformer('all-MiniLM-L6-v2')

def erstelle_chunks(text, max_zeichen=1000):
    woerter = text.split() 
    fertige_chunks = []
    aktueller_chunk = ""

    for wort in woerter:
        if (len(aktueller_chunk) + len(wort)) > max_zeichen:
            fertige_chunks.append(aktueller_chunk.strip())
            aktueller_chunk = wort + " "
        else: 
            aktueller_chunk += wort + " "
            
    if aktueller_chunk.strip() != "":
        fertige_chunks.append(aktueller_chunk.strip())
        
    return fertige_chunks

def vektoren_erstellen(chunks):
    vektoren = modell.encode(chunks)
    return vektoren


def suche(frage, chunks, chunk_vektoren, anzahl=5):
    fragevektor = modell.encode(frage)
    chunk_vektoren = torch.tensor(chunk_vektoren)
    such_ergebnisse = util.semantic_search(fragevektor, chunk_vektoren, top_k=anzahl)
    best_texts = []

    for ergebniss in such_ergebnisse[0]:
        id = ergebniss['corpus_id']
        best_texts.append(chunks[id])
    return best_texts


