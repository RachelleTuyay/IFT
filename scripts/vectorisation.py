#! /usr/bin/env python3

"""
Ce script a été récupéré du cours de Fouile de Texte 
"""

import argparse
import ast
import pathlib
import re
import sys

from collections import Counter


REPRESENTATIONS = ("booléenne", "occurrences")
DATATYPES = ("caractères", "tokens")


def read(filename, encoding="utf-8"):
    return pathlib.Path(filename).read_text(encoding=encoding)


def read_lines_set(filename, encoding="utf-8"):
    with open(filename, encoding=encoding) as in_stream:
        return set(line.strip() for line in in_stream)


def prompt(choices, nom):
    enums = list(enumerate(choices, 1))
    indices = tuple(str(item[0]) for item in enums)
    question = f"\n{nom} à utiliser :\n" \
                + "\n".join(f"    * {item[1]} (taper {item[0]})" for item in enums) \
                + "\n? "

    selection = None
    while selection not in indices:
        selection = input(question)

    return choices[int(selection)-1]


def _process(class_dirs, mots_vides, representation="occurrences", lexicon=None, datatype="tokens"):
    contents = {
        d.name: [bag_of_words(read(f), mots_vides, datatype) for f in files]
        for d, files in class_dirs
    }
    if lexicon is None:
        lexicon = sorted(
            set(
                w
                for bows in contents.values()
                for b in bows
                for w in b.keys()
                if w and w not in mots_vides
            )
        )
    class_names = sorted(contents.keys())
    return (
        lexicon,
        class_names,
        ([*vec(b, lexicon, representation), c] for c in class_names for b in contents[c]),
    )


def nettoyage(texte):
    texte = re.sub(r"[&%!?\|_\"(){}\[\],.;/\\:§»«”“‘…–—−]+", " ", texte)
    texte = re.sub(r"\d+", "", texte)
    texte = texte.replace("\\", " ")
    texte = texte.replace("’", "'")
    texte = texte.replace("'", "' ")
    return texte


def bag_of_words(text, mots_vides, datatype="tokens"):
    text = nettoyage(text)
    if datatype == "caractères":
        return Counter(w for w in text if w and not w.isspace() and w not in mots_vides)
    elif datatype == "tokens":
        return Counter(w for w in text.lower().split() if w and w not in mots_vides)
    elif datatype not in DATATYPES:
        raise ValueError(f"datatype incorrecte: {datatype}, attendu: {DATATYPES}")
    else:
        raise NotImplementedError(f"datatype non gérée: {datatype}")


def vec(bow, lexicon, representation):
    vecteur = [bow.get(m, 0) for m in lexicon]

    if representation == "booléenne":
        vecteur = [1 if v else 0 for v in vecteur]
    elif representation == "occurrences":
        pass
    elif representation not in REPRESENTATIONS:
        raise ValueError(f"représentation incorrecte: {representation}, attendu: {REPRESENTATIONS}")
    else:
        raise NotImplementedError(f"représentation non gérée: {representation}")

    return vecteur


def process(
    corpus_path,
    out_path=None,
    representation="occurrences",
    fichier_mots_vides=None,
    lexicon=None,
    datatype="tokens",
):
    dossier = pathlib.Path(corpus_path)

    out_path = out_path or dossier.parent / "fichier-resultat.arff"

    if fichier_mots_vides is None:
        mots_vides = set()
    else:
        mots_vides = read_lines_set(fichier_mots_vides, encoding="utf-8")

    if lexicon is not None:
        if lexicon.endswith(".arff"):
            with open(lexicon, encoding="utf-8") as in_stream:
                lexicon = sorted(
                    set(
                        word
                        for l in in_stream
                        if l.startswith("@attribute")
                        # unescape (quoted) string
                        for word in (
                            ast.literal_eval((re.search(r"'.*'", l).group(0))),
                        )
                        if word != "xClasse"
                    )
                )
        else:
            lexicon = sorted(read_lines_set(lexicon, "utf-8"))

    # Chaque sous-dossier (non-caché) du dossier principal est une étiquette de classe
    class_dirs = (
        (d, sorted(f for f in d.glob("*.txt") if not f.name.startswith(".")))
        for d in dossier.iterdir()
        if d.is_dir and not d.name.startswith(".")
    )
    lexicon, class_names, rows = _process(
        class_dirs, mots_vides, representation, lexicon, datatype=datatype
    )

    # Écriture des donnees au format .arff dans la variable `sortie`
    sortie = ["@relation corpus"]
    for mot in lexicon:
        sortie.append("@attribute '{m}' numeric".format(m=mot.replace("'", r"\'")))
    sortie.append(f"@attribute 'xClasse' {{{','.join(class_names)}}}")
    sortie.append("@data")
    for r in rows:
        sortie.append(",".join(map(str, r)))

    # ecriture du contenu de la variable dans le fichier de sortie
    with open(out_path, "w", encoding="utf-8") as fichier_sortie:
        fichier_sortie.write("\n".join(sortie))
        fichier_sortie.write("\n")

    print(f"{out_path} produit !")


def main_entry_point(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        parser = argparse.ArgumentParser(
            description="Transforme un corpus sous la forme « un fichier par document » en fichier arff lisible par Weka"
        )
        parser.add_argument(
            "corpus_path",
            metavar="dossier_corpus",
            type=str,
            help="Le dossier contenant le corpus (un sous-dossier par classe)",
        )
        parser.add_argument(
            "out_path",
            metavar="fichier_sortie",
            nargs="?",
            type=str,
            default=None,
            help="Le chemin du fichier de sortie",
        )
        parser.add_argument(
            "--mots-vides",
            metavar="fichier_mots_vides",
            type=str,
            default=None,
            help="Un fichier contenant une liste de mots vides (un par ligne)",
        )
        parser.add_argument(
            "--lexicon",
            metavar="fichier_lexique",
            type=str,
            default=None,
            help="Un fichier contenant un lexique (un mot par ligne ou arff)",
        )
        parser.add_argument(
            "--representation",
            type=str,
            choices=REPRESENTATIONS,
            default=REPRESENTATIONS[1], # "occurrences"
            help="Quelle représentation des valeurs utiliser ?",
        )
        parser.add_argument(
            "--datatype",
            type=str,
            choices=DATATYPES,
            default=DATATYPES[1], # "tokens"
            help="Segmenter en tokens ou caractères (par exemple pour les langues logographiques)",
        )

        args = parser.parse_args(argv)
        return process(
            args.corpus_path,
            args.out_path,
            args.representation,
            args.mots_vides,
            args.lexicon,
            datatype=args.datatype,
        )

    # Legacy interactive mode
    print("Mode interactif (legacy). Utiliser `vectorisation.py -h` pour le mode CLI.`")
    corpus_path = input("Nom du dossier contenant le corpus : ")
    fichier_mots_vides = input("Nom du fichier de mots vides (se terminant par .txt) : ")
    if not fichier_mots_vides:
        fichier_mots_vides = None

    representation = prompt(REPRESENTATIONS, "représentation")

    datatype = prompt(DATATYPES, "type de données")

    return process(
        corpus_path,
        representation=representation,
        datatype=datatype,
        fichier_mots_vides=fichier_mots_vides
    )


if __name__ == "__main__":
    sys.exit(main_entry_point(sys.argv[1:]))
