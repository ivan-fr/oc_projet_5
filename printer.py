from copy import deepcopy
from managers import ApiOperatorManager, DatabaseManager
from termcolor import cprint
from math import ceil


def _find_words(string: str):
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


class Printer:
    product_url = "https://fr.openfoodfacts.org/product/{}"
    store_department = {
        'Prêt à deguster': ('Sandwichs', 'Desserts', 'Entrées'),
        'Fruits et Légumes': ('Fruits', 'Légumes frais'),
        'Viande et Poissons': ({
            'boucherie': ('Viandes fraîches', 'Bœuf', 'Viandes de veau', 'Porc'),
            'Poissonnerie': ('Fruits de mer', 'Sushi')
        }),
        'Pains et Pâtisseries': ('Pain', 'Gâteaux'),
        'Crémerie': ('Œufs', 'Crèmes fraîches', 'Laits', 'Boissons lactées',
                     {
                         'Fromages': (
                             'Raclettes', 'Camemberts', 'Coulommiers', 'Bries', 'Roqueforts', 'Fromages de brebis',
                             'Mozzarella', 'Feta', 'Emmentals', 'Comté', 'Cantal', 'Fromages en tranches',
                             'Fromages râpés'),
                         'Yaourts, desserts et spécialités végétales': ('Fromages blancs', 'Yaourts natures',
                                                                        'Yaourts aux fruits',
                                                                        'Fromages blancs aux fruits',
                                                                        'Yaourts à boire', 'Mousses sucrées',
                                                                        'Yaourts au Bifidus'),
                         'Beurres et margarines': ('Beurres doux', 'Beurres demi-sel', 'Margarines')
                     }),
        'Charcuterie': ('Foies gras', 'Jambons blancs', 'Rôtis de porc', 'Saucissons', 'Chorizos',
                        'Lardons de porc', 'Knacks industrielles', 'Saucisses', 'boudins'),
        'Epicerie Salée': ({
                               "Pour l'apéritif": ('Chips', 'Cacahuètes', 'Olives', 'Tuiles salées',
                                                   'Tortillas', 'Biscuits apéritifs', 'Pistaches'),
                               'Soupes et croutons': ('Soupes', 'Soupes déshydratées', 'Croûtons'),
                               'Les Plats cuisinés': ('Raviolis au bœuf', 'Couscous préparés', 'Taboulés',
                                                      'Cassoulets', 'Confits de canard', 'Choucroutes'),
                               'Conserves et bocaux': (
                                   'Maïs', 'Asperges', 'Macédoines de légumes en conserve', 'Ratatouilles',
                                   'Champignons en conserve', 'Tomates en conserve', 'Thons en conserve',
                                   'Sardines en conserve'),
                               'Huiles, vinaigres, condiments et sauces': (
                                   "Huiles d'olive", "Huiles de tournesol", "Vinaigres",
                                   "Vinaigrettes", "Jus de citron", "Cornichons",
                                   "Olives", "Moutardes", "Ketchup", "Mayonnaises"),
                               'Sel, épices et bouillons': (
                                   'Sels', 'Poivres', 'Epices', 'Herbes aromatiques', 'Bouillons')
                           }, 'Pâtes alimentaires', 'Riz'),
        'Epicerie Sucrée': ('Bonbons', 'Confiseries chocolatées', 'Confiseries', 'Céréales pour petit-déjeuner',
                            'Barres de céréales', 'Pains de mie', 'Confitures', 'Pâtes à tartiner', 'Biscuits',
                            {
                                'Compotes, fruits au sirop et crèmes desserts': ('Compotes', 'Fruits au sirop',
                                                                                 'Crèmes dessert'),
                                'Sucres, farines, coulis et préparation gâteaux': ('Sucres', 'Farines'),
                                'Diététique': ('Produits sans gluten', 'Boissons sucrées', 'Thés')
                            }),
        'Surgelés': ('Pizzas', 'Pizzas et tartes surgelées', 'Frites surgelées',
                     {'Glaces et sorbets': ('Crèmes glacées', 'Bâtonnets glacés',
                                            'Cônes', 'Bûches glacées', 'Glaces et sorbets')})
    }

    def __init__(self):
        self.api_operator = ApiOperatorManager()

    def __call__(self, *args, **kwargs):
        self.database_manager = DatabaseManager()

        # Init main loop for the application.
        while True:
            cprint(' Menu ', 'white', 'on_red')
            print("==================")
            cprint(' 1) Quel aliment souhaitez-vous remplacer ? ', 'white', 'on_blue')
            cprint(' 2) Retrouver mes aliments substitués. ', 'white', 'on_blue')

            reply_1 = self.ask_with_input(2, ('quit',))

            if reply_1 == 'quit':
                break
            elif reply_1 == '1':
                while True:
                    cprint(' 1) Parcourir le rayon. ', 'white', 'on_blue')
                    cprint(' 2) Effectuer uen recherche. ', 'white', 'on_blue')

                    reply_2 = self.ask_with_input(2, ('quit',))

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
        departments = tuple(self.store_department.keys())

        while True:
            print('Choisir un rayon :')

            position, step, reply_3 = "", "", None

            for i, department in enumerate(departments, start=1):
                cprint(str(i) + ') ' + department + ' >', 'blue')

            reply_1 = self.ask_with_input(len(departments), ('quit',))

            if reply_1 == 'quit':
                break

            position += 'dict:' + str(departments[int(reply_1) - 1])
            step += "1"

            while True:
                data = self.__get_sub_department(position)

                sub_department = data[0]

                for i, department in enumerate(sub_department, start=1):
                    if isinstance(department, dict):
                        cprint(str(i) + ') ' + department["value"], 'blue')
                    else:
                        cprint(str(i) + ') ' + department, 'blue')

                reply_2 = self.ask_with_input(len(sub_department), ('quit', 'back'))

                if reply_2 == 'quit':
                    break

                if reply_2 == 'back':
                    position = "|".join(position.split('|')[:-int(step[-1])])
                    step = step[:-1]

                    if not position:
                        break
                else:
                    department_number = int(reply_2) - 1
                    if data[1] is not None and isinstance(sub_department[department_number], dict):
                        position += "|tuple:" + str(data[1])
                        position += "|dict:" + str(sub_department[department_number]["key_in_dict"])
                        step += "2"
                    else:
                        page = 1
                        while True:
                            data = self.api_operator.get_products_from_category(sub_department[department_number], page)
                            number_page = int(ceil(data['count'] / 20))
                            cprint(str(number_page) + " page(s) pour " + str(data['count']) + " résultat(s).")

                            print('Choisir un produit :')
                            products = data['products']

                            range_param = 1
                            for i, product in enumerate(products, start=1):
                                range_param = i
                                cprint(str(i) + ') ' + product.get('product_name', '') + ' - '
                                       + product.get('generic_name', ''), 'blue')

                            print('page ' + str(page) + ' sur ' + str(number_page))

                            reply_3 = self.ask_with_input(range_param, ('quit', 'pp', 'ps'))

                            if reply_3 == 'quit':
                                break
                            elif reply_3 == "ps":
                                if page <= number_page - 1:
                                    page += 1
                            elif reply_3 == "pp":
                                if page >= 2:
                                    page -= 1
                            else:
                                product_number = int(reply_3) - 1
                                self.render(products[product_number])

                if reply_3 == 'quit':
                    break

    def __get_sub_department(self, position: str):
        detail_depth = position.split('|')

        select = self.store_department
        for p in range(len(detail_depth)):
            type_position = detail_depth[p].split(':')
            if type_position[0] == "tuple":
                select = select[int(type_position[1])]
            elif type_position[0] == "dict":
                select = select[type_position[1]]

        _list = []
        dict_index_in_tuple = None

        for i, department in enumerate(select):
            if isinstance(department, dict):
                dict_index_in_tuple = i
                keys = []
                for key in department.keys():
                    keys.append({"value": key + ' > ', "key_in_dict": key})
                _list.extend(keys)
            else:
                _list.append(department)

        return _list, dict_index_in_tuple

    def get_substitutable_products(self):
        """Get substitutable products"""
        while True:
            products = self.database_manager.get_substitutable_products()

            if not products:
                cprint('Aucun resultat.', 'red')
                return

            print('Choisir un produit :')

            range_param = 1

            for i, product in enumerate(products, start=1):
                range_param = i
                cprint(str(i) + ') ' + product.get('product_name', '') + ' - ' + product.get('generic_name', ''),
                       'blue')

            reply = self.ask_with_input(range_param, ('quit',))

            if reply == 'quit':
                break

            product_number = int(reply)
            product_number -= 1
            product = products[product_number]

            operateur_result = []
            self.database_manager.fill_list_with_product_and_substitutes(product.get('id'), operateur_result)
            # print product and his subsitutes in the terminal
            self.printer(operateur_result)

    def do_research(self):
        """Research function."""
        while True:
            research = " ".join(_find_words(str(input('Taper votre recherche (tapez "quit" pour quitter) : '))))
            if research == "quit":
                break

            # get products with research from openfoodfacts api
            products = self.api_operator.get_products(research)
            if not products:
                cprint("Aucun résultat.", "red")
                continue

            print('Choisir un produit :')

            range_param = 1
            for i, product in enumerate(products, start=1):
                range_param = i
                cprint(str(i) + ') ' + product.get('product_name', '') + ' - ' + product.get('generic_name', ''),
                       'blue')

            reply = self.ask_with_input(range_param, ('quit',))

            if reply == 'quit':
                continue

            product_number = int(reply) - 1
            self.render(products[product_number])

    def render(self, product: dict):
        # wash categories_tag and categories
        i = 0
        while i <= len(product['categories_tags']) - 1:
            if ':' in product['categories_tags'][i]:
                product['categories_tags'][i] = (product['categories_tags'][i].split(':'))[1]
            i += 1
        product['categories'] = product['categories'].split(',')
        i = 0
        while i <= len(product['categories']) - 1:
            if ':' in product['categories'][i]:
                product['categories'][i] = (product['categories'][i].split(':'))[1]
            i += 1
        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        procedure_result = self.database_manager.check_if_product_exist_by_bar_code(product['code'])
        if procedure_result[1]:
            # if product already exist in database p_researched_subsitutes = 0
            print('Produit déjà présent dans la base de données.')
            # if product doesn't have substitutes in database
            if not procedure_result[2] and not procedure_result[3]:
                # get substitutes of the current product from the openfoodfacts API
                substitutes = self.api_operator.get_substitutes(product['categories_tags'][-1],
                                                                product.get('nutrition_grade', 'e'))
                self.database_manager.save_substitutes_sql_database(procedure_result[1], substitutes)
            operateur_result = []
            self.database_manager.fill_list_with_product_and_substitutes(procedure_result[1], operateur_result)
            self.printer(operateur_result)
        else:
            # get substitutes of the current product from the openfoodfacts API.
            substitutes = self.api_operator.get_substitutes(product['categories_tags'][-1],
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
                self.database_manager.save_product_sql_database(product, substitutes)
                cprint('Produit enregistré dans la base de données.', 'red')

    @staticmethod
    def printer_adapter_for_terminal(products: list):
        """Join each list in the given product from the openfoodfacts API for the printer function"""
        for product in products:
            product['categories'] = ', '.join(product.get('categories', ()))
            product['brands_tags'] = ', '.join(product.get('brands_tags', ()))
            product['ingredients'] = ', '.join(ingredient['text'] for ingredient in product.get('ingredients', ()))
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
                  '|', Printer.product_url.format(product['code']))
            print("nom généric :", product.get('generic_name'))
            print("marques :", product['brands_tags'])
            print('nutrition grade :', product['nutrition_grades'].upper())
            print('categories :', product['categories'])
            print('ingredients :', product['ingredients'])
            print('magasins :', product['stores_tags'])
        cprint("==================", 'blue')
        print()

    @staticmethod
    def ask_with_input(range_param: int, str_choices: tuple):
        # a loop for input choices
        while True:
            reply = input('Choisir un numéro (tapez "quit" pour quitter) : ')
            try:
                if reply not in str_choices:
                    if int(reply) not in range(1, range_param + 1):
                        continue
            except ValueError:
                continue
            break

        return reply
