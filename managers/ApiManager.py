import re
import requests
from slugify import slugify


class ApiManager:
    """this class communicates with the api of openfoodfacts"""

    # Init url from openfoodfacts api.
    search_url = "https://fr.openfoodfacts.org/cgi/search.pl"
    product_url = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    category_url = "https://fr.openfoodfacts.org/categorie/{}/{}.json"
    marks_for_a_category_url = "https://fr.openfoodfacts.org/categorie" \
                               "/{}/notes-nutritionnelles.json"
    product_marks_url = "https://fr.openfoodfacts.org/categorie/{}" \
                        "/note-nutritionnelle/{}.json"

    def get_products(self, research: str):
        """Get products from the openfoodfacts API by research"""

        payload = {'search_terms': research, 'search_simple': 1,
                   'action': 'process', 'page_size': 20, 'json': 1}
        request = requests.get(self.search_url, params=payload,
                               allow_redirects=False)

        if request.status_code == 301:
            print(request.next.path_url)
            numero_product = re.search(
                r'^/(produit|product)/(\d+)/?[0-9a-zA-Z_\-]*/?$',
                request.next.path_url).group(2)
            request = requests.get(self.product_url.format(numero_product))
            request = (request.json()['product'],)
        else:
            request = request.json()

            if request['count'] > 0:
                request = request['products']
            else:
                return None

        return request

    def get_substitutes(self, category: str, nutrition_grades: str):
        """Get the best substitutes for a category"""

        substitutes = []
        r2 = requests.get(
            self.marks_for_a_category_url.format(slugify(category)),
            allow_redirects=False)

        if r2.status_code == 301:
            category = re.search(r'^/categorie/([0-9a-z_\-]*).json$',
                                 r2.next.path_url).group(1)
            r2 = requests.get(
                self.marks_for_a_category_url.format(category))

        r2 = r2.json()

        if r2['count'] > 0:
            i_substitutes, i_mark = 0, 0
            while i_substitutes <= 4 and i_mark <= r2['count'] - 1 and \
                    r2['tags'][i_mark]['id'] < nutrition_grades:
                r3 = requests.get(
                    self.product_marks_url.format(slugify(category),
                                                  r2['tags'][i_mark]['id']))
                r3 = r3.json()
                substitutes += r3['products'][:5 - i_substitutes]
                i_substitutes += len(r3['products'][:5 - i_substitutes])
                i_mark += 1

        # wash categories keys
        for substitute in substitutes:
            substitute['categories'] = substitute['categories'].split(',')
            i = 0
            while i <= len(substitute['categories']) - 1:
                if ':' in substitute['categories'][i]:
                    substitute['categories'][i] = \
                        (substitute['categories'][i].split(':'))[1]
                i += 1

        return substitutes

    def get_products_from_category(self, category: str, page: int):
        """Get products from a category"""

        r = requests.get(self.category_url.format(slugify(category), page))
        return r.json()
