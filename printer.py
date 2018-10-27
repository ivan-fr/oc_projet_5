from copy import deepcopy
from database_manager import DatabaseManager
from api_operator import ApiOperator
from termcolor import cprint


def _find_words(string):
    """Get words from a sentence."""
    if string:
        cursor, i, string = 0, 0, string + " "
        while i <= len(string) - 1:
            if string[i] in (' ', '\n', ',', '.', ')', ']'):
                if i - 1 >= cursor:
                    yield string[cursor:i]
                delta = 1
                while i + delta <= len(string) - 1:
                    if string[i + delta] not in (' ', '\n', ',', '.', '?', '!', '[', ']', '(', ')'):
                        break
                    delta += 1
                i = cursor = i + delta
            i += 1


class Printer(object):
    product_url = "https://fr.openfoodfacts.org/product/{}"

    def __init__(self):
        self.api_operator = ApiOperator()

    def __call__(self, *args, **kwargs):
        self.database_manager = DatabaseManager()

        # Init main loop for the application.
        while True:
            cprint('1) Remplacer un aliment.', 'white', 'on_blue')
            cprint('2) Retrouver mes aliments substituables.', 'white', 'on_blue')

            # Logical input choices
            while True:
                command_choice = str(input('Choisir une commande (tapez "quit" pour quitter) : '))
                if command_choice not in ('1', '2', 'quit'):
                    continue
                break

            if command_choice == 'quit':
                break
            elif command_choice == '1':
                self.research()
            else:
                self.get_substitutable_products()

        self.database_manager.close()

    def get_substitutable_products(self):
        """Get substitutable products"""
        products = self.database_manager.get_substitutable_products()

        if not products:
            cprint('Aucun resultat.', 'red')
            return

        print('Choisir un produit :')

        range_param = 1
        for i, product in enumerate(products, start=1):
            range_param = i
            cprint(str(i) + ') ' + product.get('product_name', '') + ' - ' + product.get('generic_name', ''), 'blue')

        # Logical input choices
        while True:
            product_number = input('Choisir un numéro de produit (tapez "quit" pour quitter) : ')
            if product_number != 'quit':
                try:
                    if not (1 <= int(product_number) <= range_param):
                        continue
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

        # print product and his subsitutes in the terminal
        self.printer(operateur_result)

    def research(self):
        """Research function."""

        while True:
            research = " ".join(_find_words(str(input('Taper votre recherche (tapez "quit" pour quitter) : '))))

            if research == "quit":
                break

            # get products from research
            products = self.api_operator._get_products(research)

            if not products:
                cprint("Aucun résultat.", "red")
                continue

            print('Choisir un produit :')
            range_param = 1
            for i, product in enumerate(products, start=1):
                range_param = i
                cprint(str(i) + ') ' + product.get('product_name', '') + ' - ' + product.get('generic_name', ''),
                       'blue')

            # Logical input choices
            while True:
                product_number = input('Choisir un numéro de produit (tapez "quit" pour quitter) : ')
                if product_number != 'quit':
                    try:
                        if not (1 <= int(product_number) <= range_param):
                            continue
                    except ValueError:
                        continue
                break

            if product_number == 'quit':
                break

            product_number = int(product_number)
            product_number -= 1
            product = products[product_number]

            # wash categories_tag
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

                # if product doesn't have substitutes in database
                if not procedure_result[2] and not procedure_result[3]:
                    # get substitutes of the current product from the openfoodfacts API
                    substitutes = self.api_operator._get_substitutes(product['categories_tags'],
                                                                     product.get('nutrition_grade', 'e'))
                    self.database_manager._execute_substitutes_sql_database(procedure_result[1], substitutes)

                self.database_manager.fill_list_from_database(procedure_result[1], operateur_result)

                self.printer(operateur_result)
            else:
                # get substitutes of the current product from the openfoodfacts API.
                substitutes = self.api_operator._get_substitutes(product['categories_tags'],
                                                                 product.get('nutrition_grade', 'e'))

                # deepcopy for a isolate change
                operateur_result = [deepcopy(product)]

                if substitutes:
                    operateur_result.extend(deepcopy(substitutes))

                self.printer_adapter_for_terminal(operateur_result)
                # print product and his subsitutes in the terminal
                self.printer(operateur_result)

                while True:
                    save_choice = str(input('Sauvergader dans la base de données ? (y/n) '))
                    if save_choice not in ('y', 'n'):
                        continue
                    break

                if save_choice == 'y':
                    # save product and his substitutes
                    self.database_manager._execute_product_sql_database(product, substitutes)
                    cprint('Produit enregistré dans la base de données.', 'red')

    def printer_adapter_for_terminal(self, products):
        """Join each list in the given product from the openfoodfacts API for the printer function"""
        for product in products:
            product['brands_tags'] = ', '.join(product.get('brands_tags', ()))
            product['ingredients'] = ', '.join(ingredient['text'] for ingredient in product.get('ingredients', ()))
            product['stores_tags'] = ', '.join(product.get('stores_tags', ()))

    def printer(self, products):
        """Print the data of a product and its substitutes."""
        print()

        i = 0
        for product in products:
            if i != 0:
                cprint("========", 'green')
                print("Substitut produit")
            else:
                cprint("==================", 'blue')
                print("Résultat produit")
                i += 1

            print(product['product_name'], '|', "code_bar :", product['code'],
                  '|', self.product_url.format(product['code']))

            print("nom généric :", product.get('generic_name'))
            print("marques :", product['brands_tags'])
            print('nutrition grade :', product['nutrition_grades'].upper())
            print('categories :', product['categories'])
            print('ingredients :', product['ingredients'])
            print('magasins :', product['stores_tags'])
        cprint("==================", 'blue')

        print()
