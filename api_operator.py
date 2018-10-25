import re
import requests
from copy import deepcopy
from slugify import slugify


from printer import Printer
from database_manager import DatabaseManager


def _find_words(string):
    """Get words from a sentence."""
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


class Operator(object):
    # Init url from openfoodfacts api.
    search_url = "https://fr.openfoodfacts.org/cgi/search.pl"
    product_json_url = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    statistics_marks_for_a_category_url = "https://fr.openfoodfacts.org/categorie/{}/notes-nutritionnelles.json"
    product_marks_url = "https://fr.openfoodfacts.org/categorie/{}/note-nutritionnelle/{}.json"

    def __init__(self):
        self.database_manager = DatabaseManager()
        self.printer = Printer()

    def __call__(self, *args, **kwargs):
        # Init main loop for the application.
        while True:
            print('1) Remplacer un aliment.')
            print('2) Retrouver mes aliments substituables.')

            # Logical input choices
            while True:
                command_choice = str(input('Choisir une commande (tapez "quit" pour quitter) : '))
                if command_choice not in ('1', '2', 'quit'):
                    continue
                break

            if command_choice == '1':
                self.research()
            elif command_choice == 'quit':
                break
            else:
                self.get_substitutable_products()

        self.database_manager.close()

    def get_substitutable_products(self):
        """Get substitutable products"""
        products = self.database_manager.get_substitutable_products()

        if not products:
            print('Aucun resultat.')
            return

        print('Choisir un produit :')

        range_param = 1
        for i, product in enumerate(products, start=1):
            range_param = i
            print(str(i) + ')', product.get('product_name', ''), '-', product.get('generic_name', ''))

        while True:
            try:
                product_number = input('Choisir un numéro de produit (tapez "quit" pour quitter) : ')
                if product_number != 'quit':
                    if not (1 <= int(product_number) <= range_param):
                        raise ValueError()
            except ValueError:
                continue
            break

        if product_number == 'quit':
            return

        product_number = int(product_number)
        product_number -= 1
        product = products[product_number]

        operateur_result = []
        self.database_manager.fill_list_from_database(product.get('id'), operateur_result)
        self.printer.printer(operateur_result)

    def research(self):
        """Research function."""

        while True:
            research = str(input('Taper votre recherche (tapez "quit" pour quitter) : '))
            research = ' '.join(_find_words(research))

            if research == "quit":
                break

            # get products from research
            products = self._get_products(research)

            if not products:
                print("Aucun résultat.")
                continue

            print('Choisir un produit :')
            range_param = 1
            for i, product in enumerate(products, start=1):
                range_param = i
                print(str(i) + ')', product.get('product_name', ''), '-', product.get('generic_name', ''))

            while True:
                try:
                    product_number = input('Choisir un numéro de produit (tapez "quit" pour quitter) : ')
                    if product_number != 'quit':
                        if not (1 <= int(product_number) <= range_param):
                            raise ValueError()
                except ValueError:
                    continue
                break

            if product_number == 'quit':
                break

            product_number = int(product_number)
            product_number -= 1
            product = products[int(product_number)]

            i = 0
            while i <= len(product['categories_tags']) - 1:
                if ':' in product['categories_tags'][i]:
                    product['categories_tags'][i] = (product['categories_tags'][i].split(':'))[1]
                i += 1

            # procedure_result[1] = p_product_id
            # procedure_result[2] = p_exist_substitutes
            # procedure_result[3] = p_researched_subsitutes
            procedure_result = self.database_manager.check_if_product_exist_by_bar_code(product['code'])

            if procedure_result[1]:
                # if product already exist in database p_researched_subsitutes = 0
                print('Produit déjà présent dans la base de données.')
                operateur_result = []

                # if product doesn't have substitutes in database and
                if not procedure_result[2] and not procedure_result[3]:
                    # get substitutes of the current product from the openfoodfacts API
                    substitutes = self._get_substitutes(product['categories_tags'], product.get('nutrition_grade', 'e'))
                    self.database_manager._execute_substitutes_sql_database(procedure_result[1], substitutes)

                self.database_manager.fill_list_from_database(procedure_result[1], operateur_result)

                self.printer.printer(operateur_result)
            else:
                # get substitutes of the current product from the openfoodfacts API.
                substitutes = self._get_substitutes(product['categories_tags'], product.get('nutrition_grade', 'e'))

                # deepcopy for a isolate change
                operateur_result = [deepcopy(product)]

                if substitutes:
                    operateur_result.extend(deepcopy(substitutes))

                self.printer.printer_adapter_for_terminal(operateur_result)
                # print product and his subsitutes in the terminal
                self.printer.printer(operateur_result)

                while True:
                    save_choice = str(input('Sauvergader dans la base de données ? (y/n) '))
                    if save_choice not in ('y', 'n'):
                        continue
                    break

                if save_choice == 'y':
                    # save product and his substitutes
                    self.database_manager._execute_product_sql_database(product, substitutes)
                    print('Produit enregistré dans la base de données.')

    def _get_products(self, research):
        """Get products from the openfoodfacts API by research"""

        words = " ".join(_find_words(research))

        payload = {'search_terms': words, 'search_simple': 1, 'action': 'process', 'page_size': 10, 'json': 1}
        request = requests.get(self.search_url, params=payload, allow_redirects=False)

        if request.status_code == 301:
            numero_product = re.search(r'^/product/(\d+)/?[0-9a-zA-Z_\-]*/?$', request.next.path_url).group(1)
            request = requests.get(self.product_json_url.format(numero_product))
            request = (request.json()['product'],)
        else:
            request = request.json()

            if request['count'] > 0:
                request = request['products']
            else:
                return None

        return request

    def _get_substitutes(self, categories, nutrition_grades):
        """Get the best substitutes for a category"""

        substitutes = None

        if not categories:
            return substitutes

        category = categories[-1]

        r2 = requests.get(self.statistics_marks_for_a_category_url.format(slugify(category)), allow_redirects=False)

        if r2.status_code == 301:
            category = re.search(r'^/categorie/([0-9a-z_\-]*).json$', r2.next.path_url).group(1)
            r2 = requests.get(self.statistics_marks_for_a_category_url.format(category))

        r2 = r2.json()

        if r2['count'] > 0 and r2['tags'][0]['id'] < nutrition_grades:
            r3 = requests.get(self.product_marks_url.format(slugify(category), r2['tags'][0]['id']))
            r3 = r3.json()
            substitutes = r3['products'][:5]

        # wash categories tags
        if substitutes:
            for substitut in substitutes:
                i = 0
                while i <= len(substitut['categories_tags']) - 1:
                    if ':' in substitut['categories_tags'][i]:
                        substitut['categories_tags'][i] = (substitut['categories_tags'][i].split(':'))[1]
                    i += 1

        return substitutes
