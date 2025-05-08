 
import os
import re
import nltk
from collections import Counter, defaultdict

# Télécharger les ressources nécessaires
nltk.download('stopwords')
from nltk.corpus import stopwords

stop_words = set(stopwords.words('french'))

def tokenize(text):
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return text.split()

def convert_corpus_to_bow_arff(corpus_dir, output_file, relation_name="BoW_Corpus"):
    docs = []
    labels = []
    word_freq = Counter()

    # Étape 1 : Tokenisation + comptage global
    for root, _, files in os.walk(corpus_dir):
        label = os.path.basename(root)
        for file in files:
            if file.endswith(".txt"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    text = f.read()
                    tokens = tokenize(text)
                    filtered = [w for w in tokens if w not in stop_words]
                    word_freq.update(filtered)
                    docs.append((filtered, label))
                    labels.append(label)

    # Étape 2 : Supprimer hapax
    hapax = {w for w, c in word_freq.items() if c == 1}
    vocab = sorted([w for w in word_freq if w not in hapax])
    vocab_index = {w: i for i, w in enumerate(vocab)}

    # Étape 3 : Vectorisation BoW
    bow_vectors = []
    for tokens, label in docs:
        vec = [0] * len(vocab)
        for w in tokens:
            if w in vocab_index:
                vec[vocab_index[w]] += 1
        bow_vectors.append((vec, label))

    # Étape 4 : Génération du fichier ARFF
    with open(output_file, "w", encoding="utf-8") as arff:
        arff.write(f"@RELATION {relation_name}\n\n")
        for word in vocab:
            arff.write(f"@ATTRIBUTE {word} NUMERIC\n")
        arff.write(f"@ATTRIBUTE class {{{','.join(sorted(set(labels)))}}}\n\n")
        arff.write("@DATA\n")
        for vec, label in bow_vectors:
            arff.write(f"{','.join(map(str, vec))},{label}\n")

    print(f"Fichier ARFF (Bag of Words) généré : {output_file}")

# Exemple d'utilisation
if __name__ == "__main__":
    convert_corpus_to_bow_arff("data/", "corpus_bow.arff")
