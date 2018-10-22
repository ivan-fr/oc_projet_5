import mysql.connector
import requests
from slugify import slugify
import re
from copy import deepcopy


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
    product_url_json = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    product_url = "https://fr.openfoodfacts.org/produit/{}"
    stats_notes_categorie = "https://fr.openfoodfacts.org/categorie/{}/notes-nutritionnelles.json"
    product_marks_url = "https://fr.openfoodfacts.org/categorie/{}/note-nutritionnelle/{}.json"

    def __init__(self):
        self.mydb = mysql.connector.connect(host="localhost",
                                            user="openfoodfacts",
                                            passwd="hWfY7Uv82k7L9f2Sr._.",
                                            database="openfoodfacts")

        self.cursor = self.mydb.cursor()

    def __call__(self, research):
        products = self._get_products(research)

        if not products:
            return 0

        print('Choisissez un produit :')
        range_param = 0
        for i, produit in enumerate(products, start=1):
            range_param = i
            print(str(i) + ')', produit.get('product_name', ''), '-', produit.get('generic_name', ''))

        while True:
            try:
                product_number = int(input('Choisissez un numéro de produit : '))
                if not (1 <= product_number <= range_param):
                    raise ValueError()
            except ValueError:
                continue
            break

        product_number -= 1
        product = products[product_number]

        i = 0
        while i <= len(product['categories_tags']) - 1:
            if ':' in product['categories_tags'][i]:
                product['categories_tags'][i] = (product['categories_tags'][i].split(':'))[1]
            i += 1

        procedure_result = self.cursor.callproc('check_if_product_exist_by_bar_code', (product['code'], 0, 0, 0))

        if procedure_result[1]:
            print('Produit déjà présent dans la base de données.')
            operateur_result = []

            if not procedure_result[2] and not procedure_result[3]:
                substitutes = self._get_substitutes(product['categories_tags'], product.get('nutrition_grade', 'e'))
                self._execute_substitutes_sql_database(procedure_result[1], substitutes)

            self.cursor.callproc('get_product_detail', (procedure_result[1],))

            for result in self.cursor.stored_results():
                operateur_result.append(dict(zip(result.column_names, result.fetchone())))

            if operateur_result[0].get('substitutes', ''):
                for substitute in str(operateur_result[0].get('substitutes', '')).split(','):
                    self.cursor.callproc('get_product_detail', (int(substitute),))

                    for result in self.cursor.stored_results():
                        operateur_result.append(dict(zip(result.column_names, result.fetchone())))

            self.printer(operateur_result)
        else:
            substitutes = self._get_substitutes(product['categories_tags'], product.get('nutrition_grade', 'e'))

            operateur_result = [deepcopy(product)]

            if substitutes:
                operateur_result.extend(deepcopy(substitutes))

            self.printer_adapter_for_terminal(operateur_result)
            self.printer(operateur_result)

            while True:
                try:
                    save_choice = str(input('Sauvergader dans la base de données ? (y/n) '))
                    if not save_choice in ('y', 'n'):
                        raise ValueError()
                except ValueError:
                    continue
                break

            if save_choice == 'y':
                self._execute_product_sql_database(product, substitutes)
                print('Produit enregistré dans la base de données.')

        return 1

    def printer_adapter_for_terminal(self, products):

        for product in products:
            product['nutrition_grades'] = ', '.join(product['nutrition_grades'])
            product['brands_tags'] = ', '.join(product['brands_tags'])
            product['categories_tags'] = ', '.join(product['categories_tags'])
            product['ingredients'] = ', '.join(ingredient['text'] for ingredient in product['ingredients'])
            product['stores_tags'] = ', '.join(product['stores_tags'])

        return products

    def printer(self, products):
        i = 0
        for product in products:
            if not i == 0:
                print("========")
                print("Substitut produit")
            else:
                print("==================")
                print("Résultat produit")
                i += 1

            print(product['product_name'], '|', "code_bar :", product['code'],
                  '|', self.product_url.format(product['code']))

            print("nom généric :", product['generic_name'])
            print("marques :", product['brands_tags'])
            print('nutrition grade :', product['nutrition_grades'].upper())
            print('categories :', product['categories_tags'])
            print('ingredients :', product['ingredients'])
            print('magasins :', product['stores_tags'])
        print("==================")

    def _get_products(self, research):
        words = " ".join(_find_words(research))

        params = {'search_terms': words, 'search_simple': 1, 'action': 'process', 'page_size': 10, 'json': 1}
        request = requests.get(self.search_url, params=params, allow_redirects=False)

        if request.status_code == 301:
            numero_produit = re.search(r'^/produit/(\d+)/?[0-9a-zA-Z_\-]*/?$', request.next.path_url).group(1)
            request = requests.get(self.product_url_json.format(numero_produit))
            request = (request.json()['product'],)
        else:
            request = request.json()

            if request['count'] > 0:
                request = request['products']
            else:
                return []

        return request

    def _get_substitutes(self, categories, nutrition_grades):
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

        if r2['count'] > 0 and r2['tags'][0]['id'] < nutrition_grades:
            r3 = requests.get(self.product_marks_url.format(slugify(categorie), r2['tags'][0]['id']))
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

    def _execute_product_sql_database(self, product, substitutes):

        procedure_result = self.cursor.callproc('check_if_product_exist_by_bar_code', (product['code'], 0, 0, 0))

        if procedure_result[1]:
            return procedure_result[1]

        sql = "INSERT INTO produit (nom, nom_generic, nutrition_grade, code_bar, code_bar_unique) " \
              "VALUES (%s, %s, %s, %s, %s);"
        val = (product.get('product_name', ''), product.get('generic_name', ''),
               product.get('nutrition_grades', 'e'), product['code'], product['code'])

        self.cursor.execute(sql, val)

        r_id = self.cursor.lastrowid

        for categorie in product.get('categories_tags', ''):
            sql = "INSERT INTO categorie (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (categorie,)
            self.cursor.execute(sql, val)

            _categorie_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_categorie (categorie_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE categorie_id = categorie_id;"
            val = (_categorie_id, r_id)
            self.cursor.execute(sql, val)

        for ingredient in product.get('ingredients', ''):
            sql = "INSERT INTO ingredient (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (ingredient['text'],)
            self.cursor.execute(sql, val)

            _ingredient_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_ingredient (ingredient_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE ingredient_id = ingredient_id;"

            val = (_ingredient_id, r_id)
            self.cursor.execute(sql, val)

        for brand in product.get('brands_tags', ''):
            sql = "INSERT INTO marque (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (brand,)
            self.cursor.execute(sql, val)

            _marque_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_marque (marque_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE marque_id = marque_id;"
            val = (_marque_id, r_id)
            self.cursor.execute(sql, val)

        for store in product.get('stores_tags', ''):
            sql = "INSERT INTO magasin (nom) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (store,)
            self.cursor.execute(sql, val)

            _store_id = self.cursor.lastrowid

            sql = "INSERT INTO produit_magasin (magasin_id, produit_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE magasin_id = magasin_id;"
            val = (_store_id, r_id)
            self.cursor.execute(sql, val)

        self.mydb.commit()

        if substitutes is not None:
            self._execute_substitutes_sql_database(r_id, substitutes)

        return r_id

    def _execute_substitutes_sql_database(self, produit_id, substitutes):
        if substitutes is not None:
            for substitution in substitutes:

                substitution_id = self._execute_product_sql_database(substitution, None)

                if produit_id != substitution_id:
                    sql = "INSERT INTO produit_substitute_produit (produit_id_1, produit_id_2) " \
                          "VALUES (%s, %s) " \
                          "ON DUPLICATE KEY UPDATE produit_id_2 = produit_id_2;"
                    val = (produit_id, substitution_id)

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
