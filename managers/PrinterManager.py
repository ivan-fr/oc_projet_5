from copy import deepcopy
from managers.ApiManager import ApiManager
from managers.DatabaseManager import DatabaseManager
from termcolor import cprint
from math import ceil
from constants import STORE_DEPARTMENT

import os


def _find_words(string: str):
    """Get words from a sentence."""
    if string:
        cursor, i, string = 0, 0, string + " "
        while i <= len(string) - 1:
            if string[i] in (' ', '\n', ',', '.', ')', ']', ';'):
                if i - 1 >= cursor:
                    yield string[cursor:i]
                delta = 1
                while i + delta <= len(string) - 1:
                    if string[i + delta] not in (
                            ' ', '\n', ',', '.', '?', '!', '[', ']', '(', ')',
                            ';'):
                        break
                    delta += 1
                i = cursor = i + delta
            i += 1


def clean_terminal():
    """clean the terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


class PrinterManager:
    """his role is to contain the logic of the flow
     of the messages to be displayed on the
    terminal"""

    product_url = "https://fr.openfoodfacts.org/product/{}"

    def __init__(self):
        self.api_operator = ApiManager()

    def __call__(self, *args, **kwargs):
        """Init main loop for the application."""

        self.database_manager = DatabaseManager()

        while True:
            clean_terminal()
            cprint(' Menu ', 'red')
            print("==================")
            cprint(' 1) Quel aliment souhaitez-vous remplacer ?', 'red')
            cprint(' 2) Retrouver mes aliments substitués.', 'red')

            reply_1 = self.ask_with_input('Choisir un numéro '
                                          '(tapez "quit" pour quitter)'
                                          ' : ', 2, ('quit',))

            if reply_1 == 'quit':
                break
            elif reply_1 == '1':
                while True:
                    clean_terminal()
                    cprint(' 1) Parcourir le rayon. ', 'red')
                    cprint(' 2) Effectuer une recherche. ', 'red')

                    reply_2 = self.ask_with_input('Choisir un numéro '
                                                  '(tapez "quit" pour quitter)'
                                                  ' : ', 2, ('quit',))

                    if reply_2 == 'quit':
                        break
                    elif reply_2 == "1":
                        self.get_store_department()
                    elif reply_2 == "2":
                        self.do_research()
            else:
                self.get_substitutable_products()

        self.database_manager.close()

    def get_store_department(self):
        """get store departments and print it"""

        departments = tuple(STORE_DEPARTMENT.keys())

        position, step = "", ""

        while True:
            clean_terminal()
            data, reply_3 = self.__get_sub_department(position), None
            sub_department = data[0]
            for i, department in enumerate(sub_department, start=1):
                if isinstance(department, dict):
                    cprint(str(i) + ') ' + department["value"], 'blue')
                else:
                    cprint(str(i) + ') ' + department, 'blue')

            reply_2 = self.ask_with_input('Choisir un numéro '
                                          '(tapez "quit" pour quitter, '
                                          '"back" pour revenir en arrière)'
                                          ' : ', len(sub_department),
                                          ('quit', 'back'))
            if reply_2 == 'quit':
                break
            if reply_2 == 'back':
                if not position:
                    break
                position = "|".join(position.split('|')[:-int(step[-1])])
                step = step[:-1]
            else:
                department_number = int(reply_2) - 1
                if data[1] is not None and isinstance(
                        sub_department[department_number], dict):
                    position += "|tuple:" + str(data[1])
                    position += "|dict:" + str(
                        sub_department[department_number]["key_in_dict"])
                    step += "2"
                elif data[1] is None and not position:
                    position += 'dict:' + str(departments[int(reply_2) - 1])
                    step += "1"
                else:
                    self.__print_products_navigation(
                        sub_department[department_number])

    @staticmethod
    def __get_sub_department(position: str):
        """get sub department from a position"""

        detail_depth = position.split('|')

        select = STORE_DEPARTMENT
        for i in range(len(detail_depth)):
            type_position = detail_depth[i].split(':')
            if type_position[0] == "tuple":
                select = select[int(type_position[1])]
            elif type_position[0] == "dict":
                select = select[type_position[1]]

        _list = []
        dict_index_in_tuple = None

        for i, department in enumerate(select):
            if isinstance(department, dict):
                dict_index_in_tuple = i
                for key in department.keys():
                    _list.append({"value": key + ' >', "key_in_dict": key})
            elif isinstance(select, dict) and isinstance(select.get(department),
                                                         tuple):
                _list.append(department + ' >')
            else:
                _list.append(department)

        return _list, dict_index_in_tuple

    def get_substitutable_products(self):
        """Get substitutable products and print it"""

        while True:
            clean_terminal()
            products = self.database_manager.get_substitutable_products()

            if not products:
                cprint('Aucun resultat.', 'red')
                return

            print('Choisir un produit :')

            range_param = self.print_products_line(products)

            reply = self.ask_with_input('Choisir un numéro'
                                        ' (tapez "quit" pour quitter) : ',
                                        range_param, ('quit',))

            if reply == 'quit':
                break

            product_number = int(reply)
            product_number -= 1
            product = products[product_number]

            operateur_result = []
            self.database_manager.fill_list_with_product_and_substitutes(
                product.get('id'), operateur_result)
            # print product and his substitutes in the terminal
            self.printer(operateur_result)

            self.ask_with_input('Ok ? (y) ', -1, ('y',))

    def do_research(self):
        """do a reasearch of product and print it"""

        while True:
            clean_terminal()
            research = " ".join(_find_words(str(
                input('Taper votre recherche (tapez "quit" pour quitter) : '))))
            if research == "quit":
                break

            # get products with research from openfoodfacts api
            products = self.api_operator.get_products(research)

            if not products:
                cprint("Aucun résultat.", "red")
                self.ask_with_input('Ok ? (y) ', -1, ('y',))
                continue

            print('Choisir un produit :')

            range_param = self.print_products_line(products)

            reply = self.ask_with_input('Choisir un numéro '
                                        '(tapez "quit" pour quitter) : ',
                                        range_param, ('quit',))

            if reply == 'quit':
                continue

            product_number = int(reply) - 1
            self.render(products[product_number])

    def render(self, product: dict):
        """ print product and his substitutes """

        clean_terminal()
        self.wash_categories(product)

        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        procedure_result = self.database_manager.check_if_product_exist(
            product['code'])
        if procedure_result[1]:  # if product already exist in database
            self.__print_from_database(product, procedure_result)
        else:
            self.__print_from_api(product)

    def __print_products_navigation(self, category):
        """print products from a category with a navigation page"""

        def input_validation(string: str):
            if string.startswith('p'):
                try:
                    int(string[1:])
                except ValueError:
                    return False
                else:
                    return True
            return False

        page = 1
        while True:
            clean_terminal()
            data = self.api_operator.get_products_from_category(
                category, page)
            number_page = int(ceil(data['count'] / 20))
            cprint(str(number_page) + " page(s) pour " + str(
                data['count']) + " résultat(s).")
            print('Choisir un produit :')

            self.print_products_line(data['products'])

            print('page ' + str(page) + ' sur ' + str(number_page))
            reply_3 = self.ask_with_input('Choisir un numéro (tapez "quit" pour'
                                          ' quitter, "pp" pour pagge précedente'
                                          ', "ps" pour page suivante, p<numéro>'
                                          ' pour aller à la page numéro) : ',
                                          20,
                                          ('quit', 'pp', 'ps'),
                                          input_validation)
            if reply_3 == 'quit':
                break
            elif reply_3.startswith('p'):
                if reply_3 == "ps":
                    if page <= number_page - 1:
                        page += 1
                elif reply_3 == "pp":
                    if page >= 2:
                        page -= 1
                else:
                    reply_3 = int(reply_3[1:])
                    if 1 <= reply_3 <= number_page:
                        page = reply_3
            else:
                product_number = int(reply_3) - 1
                self.render(data['products'][product_number])

    def __print_from_database(self, product: dict, procedure_result: list):
        """print the product and his substitutes
         from the database  """

        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes

        print('Produit déjà présent dans la base de données.')
        # if product doesn't have substitutes in database
        if not procedure_result[2] and not procedure_result[3]:
            # get substitutes of the current product
            # from the openfoodfacts API
            substitutes = self.api_operator.get_substitutes(
                product['categories_tags'][-1],
                product.get('nutrition_grades', 'e'))
            self.database_manager.save_substitutes_sql_database(
                procedure_result[1], substitutes)
        operateur_result = []
        self.database_manager.fill_list_with_product_and_substitutes(
            procedure_result[1], operateur_result)
        self.printer(operateur_result)
        self.ask_with_input('Ok ? (y) ', -1, ('y',))

    def __print_from_api(self, product: dict):
        """ print substitutes of the current product
         from the openfoodfacts API """

        substitutes = self.api_operator.get_substitutes(
            product['categories_tags'][-1],
            product.get('nutrition_grades', 'e'))

        # deepcopy for a isolate change
        operateur_result = [deepcopy(product)]

        if substitutes:
            operateur_result.extend(deepcopy(substitutes))

        self.adapter_for_terminal(operateur_result)

        # print product and his subsitutes in the terminal
        self.printer(operateur_result)

        save_choice = self.ask_with_input(
            'Enregistrer dans la base de données ?'
            ' (y, n)', -1, ('y', 'n'))

        if save_choice == 'y':
            # save product and his substitutes
            self.database_manager.save_product(product, substitutes)
            cprint('Produit enregistré dans la base de données.', 'red')

    @staticmethod
    def wash_categories(product: dict):
        """wash categories_tag and categories"""

        i = 0
        while i <= len(product['categories_tags']) - 1:
            if ':' in product['categories_tags'][i]:
                product['categories_tags'][i] = \
                    (product['categories_tags'][i].split(':'))[1]
            i += 1

        product['categories'] = product['categories'].split(',')
        i = 0
        while i <= len(product['categories']) - 1:
            if ':' in product['categories'][i]:
                product['categories'][i] = \
                    (product['categories'][i].split(':'))[1]
            i += 1

    @staticmethod
    def adapter_for_terminal(products: list):
        """Join each list in the given product from the
        openfoodfacts API for the printer function"""

        for product in products:
            product['categories'] = ', '.join(product.get('categories', ()))
            product['brands_tags'] = ', '.join(product.get('brands_tags', ()))
            product['ingredients'] = ', '.join(
                ingredient['text'] for ingredient in
                product.get('ingredients', ()))
            product['stores_tags'] = ', '.join(product.get('stores_tags', ()))

    @staticmethod
    def printer(products: list):
        """Print the data of a product and its substitutes."""
        print()
        i = 0
        for product in products:
            if i != 0:
                cprint("=========", 'green')
                print("Substitut produit")
            else:
                cprint("==================", 'blue')
                print("Résultat produit")
                i += 1
            print(product['product_name'], '|', "code_bar :", product['code'],
                  '|', PrinterManager.product_url.format(product['code']))
            print("nom généric :", product.get('generic_name'))
            print("marques :", product['brands_tags'])
            print('nutrition grade :', product.get('nutrition_grades',
                                                   'pas de grade'))
            print('categories :', product['categories'])
            print('ingredients :', product['ingredients'])
            print('magasins :', product['stores_tags'])
        cprint("==================", 'blue')
        print()

    @staticmethod
    def ask_with_input(string, range_param: int, str_choices: tuple,
                       custom_validation: (callable, None) = None):
        """a loop for input choices"""
        while True:
            reply = input(string)
            try:
                if reply not in str_choices and not (
                        custom_validation is not None and custom_validation(
                        reply)):
                    if range_param <= 0:
                        continue
                    elif int(reply) not in range(1, range_param + 1):
                        continue
            except ValueError:
                continue
            break

        return reply

    def print_products_line(self, products: list):
        """ print products line for the selection input """

        range_param = 1

        products = deepcopy(products)

        self.adapter_for_terminal(products)

        for i, product in enumerate(products, start=1):
            range_param = i

            _str = str(i) + ") "

            if product.get('product_name'):
                _str += product.get('product_name')
            if product.get('generic_name'):
                _str += " - " + product.get('generic_name')
            if product.get('brands_tags'):
                _str += " - marques : (" + product.get('brands_tags') + ")"

            cprint(_str, 'blue')

        return range_param
