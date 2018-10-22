from mysql_operateur import Operateur


operateur = Operateur()

while True:
    recherche = input('Tapez votre recherche : ')
    resultat = []

    if recherche == "quit":
        break

    if recherche:
        resultat = operateur(recherche)

    if not resultat:
        print("Aucun résultat")

    print()

operateur.close()
