class Printer(object):
    product_url = "https://fr.openfoodfacts.org/product/{}"

    def printer_adapter_for_terminal(self, products):
        """Join each list in the given product from the openfoodfacts API."""
        for product in products:
            product['nutrition_grades'] = ', '.join(product.get('nutrition_grades', ()))
            product['brands_tags'] = ', '.join(product.get('brands_tags', ()))
            product['categories_tags'] = ', '.join(product.get('categories_tags', ()))
            product['ingredients'] = ', '.join(ingredient['text'] for ingredient in product.get('ingredients', ()))
            product['stores_tags'] = ', '.join(product.get('stores_tags', ()))

    def printer(self, products):
        """Print the data of a product and his substitutes."""
        print()

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

            print("nom généric :", product.get('generic_name'))
            print("marques :", product['brands_tags'])
            print('nutrition grade :', product['nutrition_grades'].upper())
            print('categories :', product['categories_tags'])
            print('ingredients :', product['ingredients'])
            print('magasins :', product['stores_tags'])
        print("==================")

        print()
