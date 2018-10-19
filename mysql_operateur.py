import mysql.connector
import requests
from slugify import slugify
import re


def _find_words(string):
    if string:
        cursor, i, string = 0, 0, string + " "
        while i <= len(string) - 1:
            if string[i] in (' ', '\n', ',', '.', ')'):
                if i - 1 >= cursor:
                    yield string[cursor:i]
                delta = 1
                while i + delta <= len(string) - 1:
                    if string[i + delta] not in (' ', '\n', ',', '.', '?', '!', '[', ']', '(', ')'):
                        break
                    delta += 1
                i = cursor = i + delta
            i += 1


class Operateur(object):
    search_url = "https://fr.openfoodfacts.org/cgi/search.pl"
    product_url = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    stats_notes_categorie = "https://fr.openfoodfacts.org/categorie/{}/notes-nutritionnelles.json"
    product_notes_url = "https://fr.openfoodfacts.org/categorie/{}/note-nutritionnelle/{}.json"

    def __init__(self):
        self.mydb = mysql.connector.connect(host="localhost",
                                            user="openfoodfacts",
                                            passwd="hWfY7Uv82k7L9f2Sr._.",
                                            database="openfoodfacts")

        self.cursor = self.mydb.cursor()

    def __call__(self, recherche):
        resultat = []
        words = " ".join(_find_words(recherche))
        result_args = self.cursor.callproc('verifier_si_produit_exist_by_match', (words, 0, 0, 0))

        if not any(result_args[1:]):
            new_produit_id = self._prepare_data_research(words)
            if not new_produit_id:
                return resultat
            result_args = (result_args[0], new_produit_id, result_args[2], result_args[3])
        elif not result_args[2] and not result_args[3]:
            self.cursor.callproc('get_produit_detail', (result_args[1],))
            resultat_secondaire = None

            for result in self.cursor.stored_results():
                resultat_secondaire = dict(zip(result.column_names, result.fetchone()))

            if resultat_secondaire:
                r = requests.get(self.product_url.format(resultat_secondaire['code_bar']))
                r = r.json()['product']

                i = 0
                while i <= len(r['categories_tags']) - 1:
                    if ':' in r['categories_tags'][i]:
                        r['categories_tags'][i] = (r['categories_tags'][i].split(':'))[1]
                    i += 1

                subs = self._get_result_of_substitute_request(r['categories_tags'], resultat_secondaire['nutrition_grade'])
                self._execute_substitutes_sql_database(result_args[1], subs)
            else:
                raise Exception('callproc get_produit_detail n\' a pas donné de résultat.')

        self.cursor.callproc('get_produit_detail', (result_args[1],))

        for result in self.cursor.stored_results():
            resultat.append(dict(zip(result.column_names, result.fetchone())))

        if resultat[0].get('substitutes', ''):
            for substitute in str(resultat[0].get('substitutes', '')).split(','):
                self.cursor.callproc('get_produit_detail', (int(substitute),))

                for result in self.cursor.stored_results():
                    resultat.append(dict(zip(result.column_names, result.fetchone())))

        return resultat

    def _prepare_data_research(self, words):
        payload = {'search_terms': words, 'search_simple': 1, 'action': 'process', 'page_size': 2, 'json': 1}
        r = requests.get(self.search_url, params=payload, allow_redirects=False)

        if r.status_code == 301:
            numero_produit = re.search(r'^/produit/(\d+)/?[0-9a-zA-Z_\-]*/?$', r.next.path_url).group(1)
            r = requests.get(self.product_url.format(numero_produit))
            r = r.json()['product']
        else:
            r = r.json()

            if r['count'] > 0:
                r = r['products'][0]
            else:
                return False

        i = 0
        while i <= len(r['categories_tags']) - 1:
            if ':' in r['categories_tags'][i]:
                r['categories_tags'][i] = (r['categories_tags'][i].split(':'))[1]
            i += 1

        subsitutions = self._get_result_of_substitute_request(r['categories_tags'], r.get('nutrition_grades', 'e'))

        return self._execute_product_sql_database(r, subsitutions)

    def _execute_product_sql_database(self, r, substitutes, deep=False):

        result_args = self.cursor.callproc('verifier_si_produit_exist_by_code_bar', (r['code'], 0, 0))

        if result_args[1]:
            return result_args[2]

        sql = "INSERT INTO produit (nom, nom_generic, nutrition_grade, code_bar, code_bar_unique) " \
              "VALUES (%s, %s, %s, %s, %s);"
        val = (
            r.get('product_name', ''), r.get('generic_name', ''), r.get('nutrition_grades', 'e'), r['code'], r['code'])

        self.cursor.execute(sql, val)

        r_id = self.cursor.lastrowid

        for categorie in r.get('categories_tags', ''):
            sql = "INSERT INTO categorie (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (categorie,)
            self.cursor.execute(sql, val)

            _categorie_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_categorie (categorie_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE categorie_id = categorie_id;"
            val = (_categorie_id, r_id)
            self.cursor.execute(sql, val)

        for dico in r.get('ingredients', ''):
            sql = "INSERT INTO ingredient (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (dico['text'],)
            self.cursor.execute(sql, val)

            _ingredient_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_ingredient (ingredient_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE ingredient_id = ingredient_id;"

            val = (_ingredient_id, r_id)
            self.cursor.execute(sql, val)

        for brand in r.get('brands_tags', ''):
            sql = "INSERT INTO marque (nom, texte) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (brand, brand)
            self.cursor.execute(sql, val)

            _marque_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_marque (marque_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE marque_id = marque_id;"
            val = (_marque_id, r_id)
            self.cursor.execute(sql, val)

        self.mydb.commit()

        if not deep:
            self._execute_substitutes_sql_database(r_id, substitutes)

        return r_id

    def _get_result_of_substitute_request(self, categories, nutrition_grades):
        substitutes = None

        # max_len = max(map(len, categories))
        # categorie = max(item for item in categories if len(item) == max_len)
        if not categories:
            return substitutes

        categorie = categories[-1]

        r2 = requests.get(self.stats_notes_categorie.format(slugify(categorie)), allow_redirects=False)

        if r2.status_code == 301:
            categorie = re.search(r'^/categorie/([0-9a-z_\-]*).json$', r2.next.path_url).group(1)
            r2 = requests.get(self.stats_notes_categorie.format(categorie))

        r2 = r2.json()

        if r2['count'] > 0 and r2['tags'][0]['id'] <= nutrition_grades:
            r3 = requests.get(self.product_notes_url.format(slugify(categorie), r2['tags'][0]['id']))
            r3 = r3.json()
            substitutes = r3['products'][:5]

        if substitutes:
            for substitut in substitutes:
                i = 0
                while i <= len(substitut['categories_tags']) - 1:
                    if ':' in substitut['categories_tags'][i]:
                        substitut['categories_tags'][i] = (substitut['categories_tags'][i].split(':'))[1]
                    i += 1

        return substitutes

    def _execute_substitutes_sql_database(self, produit_id, substitutes):
        if substitutes is not None:
            for substitution in substitutes:

                substitution_id = self._execute_product_sql_database(substitution, None, True)

                if produit_id != substitution_id:
                    sql = "INSERT INTO produit_substitute_produit (produit_id_1, produit_id_2, best) " \
                          "VALUES (%s, %s, %s) " \
                          "ON DUPLICATE KEY UPDATE produit_id_2 = produit_id_2;"
                    val = (produit_id, substitution_id, substitution_id)

                    self.cursor.execute(sql, val)

        sql = "UPDATE produit SET research_substitutes = %s WHERE id = %s"
        val = (1, produit_id)
        self.cursor.execute(sql, val)

        self.mydb.commit()

    def close(self):
        self.cursor.close()
        self.mydb.close()


if __name__ == '__main__':
    operateur = Operateur()
    print(operateur('3297760097280'))
