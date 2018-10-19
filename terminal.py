from mysql_operateur import Operateur


def printer(produit, substitut=False):
    if substitut:
        print("========")
        print("substitut produit :", produit['produit_nom'], '|', "code_bar :", produit['code_bar'])
    else:
        print("==================")
        print("Résultat produit :", produit['produit_nom'], '|', "code_bar :", produit['code_bar'])

    print("nom généric :", produit['produit_nom_generic'])
    print("marques :", produit['marques'])
    print('nutrition grade :', produit['nutrition_grade'].upper())
    print('categories :', produit['categories'])
    print('ingredients :', produit['ingredients'])


operateur = Operateur()

while True:
    recherche = input('Tapez votre recherche : ')
    resultat = []

    if recherche == "quit":
        break

    if recherche:
        resultat = operateur(recherche)

    if resultat:
        produit = resultat[0]
        printer(produit)

        for subs in resultat[1:]:
            printer(subs, True)
    else:
        print("Aucun résultat")

    print("==================")
    print()

operateur.close()