import re
import requests
from slugify import slugify


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


class ApiOperator(object):
    # Init url from openfoodfacts api.
    search_url = "https://fr.openfoodfacts.org/cgi/search.pl"
    product_json_url = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    statistics_marks_for_a_category_url = "https://fr.openfoodfacts.org/categorie/{}/notes-nutritionnelles.json"
    product_marks_url = "https://fr.openfoodfacts.org/categorie/{}/note-nutritionnelle/{}.json"

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
        print('------------>', category)

        r2 = requests.get(self.statistics_marks_for_a_category_url.format(slugify(category)), allow_redirects=False)

        if r2.status_code == 301:
            category = re.search(r'^/categorie/([0-9a-z_\-]*).json$', r2.next.path_url).group(1)
            r2 = requests.get(self.statistics_marks_for_a_category_url.format(category))

        r2 = r2.json()

        if r2['count'] > 0 and r2['tags'][0]['id'] < nutrition_grades:
            r3 = requests.get(self.product_marks_url.format(slugify(category), r2['tags'][0]['id']))
            r3 = r3.json()
            substitutes = r3['products'][:5]

        return substitutes
