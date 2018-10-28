from constants import *
import mysql.connector


class DatabaseManager(object):
    def __init__(self):
        # Connect to the mysql database.
        self.mydb = mysql.connector.connect(host=DB_HOST,
                                            user=DB_USER,
                                            passwd=DB_PWD,
                                            database=DB_NAME)

        self.cursor = self.mydb.cursor()

    def get_substitutable_products(self):
        """Get substitutable products from database"""

        self.cursor.execute("SELECT * FROM V_get_substitutable_products")
        fetchall_result = self.cursor.fetchall()
        columns = [column[0] for column in self.cursor.description]

        products = []
        for i, product in enumerate(fetchall_result, start=1):
            products.append(dict(zip(columns, product)))

        return products

    def get_product_detail(self, product_id):
        self.cursor.callproc('get_product_detail', (product_id,))

        for result in self.cursor.stored_results():
            return dict(zip(result.column_names, result.fetchone()))

    def check_if_product_exist_by_bar_code(self, code_product):
        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        return self.cursor.callproc('check_if_product_exist_by_bar_code', (code_product, 0, 0, 0))

    def fill_list_from_database(self, product_id, products):
        """Fill a given list with the product and his substitutes from the database."""

        products.append(self.get_product_detail(product_id))

        if products[0].get('substitutes', ''):
            for substitute_id in str(products[0].get('substitutes', '')).split(','):
                products.append(self.get_product_detail(substitute_id))

    def _execute_product_sql_database(self, product, substitutes):
        # Save a product and his substitutes in the database.

        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        procedure_result = self.cursor.callproc('check_if_product_exist_by_bar_code', (product['code'], 0, 0, 0))

        if procedure_result[1]:
            return procedure_result[1]

        sql = "INSERT INTO product (product_name, generic_name, nutrition_grades, bar_code_unique) " \
              "VALUES (%s, %s, %s, %s);"
        val = (product.get('product_name', ''), product.get('generic_name', ''),
               product.get('nutrition_grades', 'e'), product['code'])

        self.cursor.execute(sql, val)

        r_id = self.cursor.lastrowid

        for category in product.get('categories', ''):
            sql = "INSERT INTO category (name) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (category,)
            self.cursor.execute(sql, val)

            _category_id = self.cursor.lastrowid

            sql = "INSERT INTO product_category (category_id, product_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE category_id = category_id;"
            val = (_category_id, r_id)
            self.cursor.execute(sql, val)

        for ingredient in product.get('ingredients', ''):
            sql = "INSERT INTO ingredient (name) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (ingredient['text'],)
            self.cursor.execute(sql, val)

            _ingredient_id = self.cursor.lastrowid

            sql = "INSERT INTO product_ingredient (ingredient_id, product_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE ingredient_id = ingredient_id;"

            val = (_ingredient_id, r_id)
            self.cursor.execute(sql, val)

        for brand in product.get('brands_tags', ''):
            sql = "INSERT INTO brand (name) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (brand,)
            self.cursor.execute(sql, val)

            _brand_id = self.cursor.lastrowid

            sql = "INSERT INTO product_brand (brand_id, product_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE brand_id = brand_id;"
            val = (_brand_id, r_id)
            self.cursor.execute(sql, val)

        for store in product.get('stores_tags', ''):
            sql = "INSERT INTO store (name) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (store,)
            self.cursor.execute(sql, val)

            _store_id = self.cursor.lastrowid

            sql = "INSERT INTO product_store (store_id, product_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE store_id = store_id;"
            val = (_store_id, r_id)
            self.cursor.execute(sql, val)

        self.mydb.commit()

        if substitutes is not None:
            self._execute_substitutes_sql_database(r_id, substitutes)

        return r_id

    def _execute_substitutes_sql_database(self, product_id, substitutes):
        # save relationship beetween products
        if substitutes is not None:
            for substitution in substitutes:

                substitution_id = self._execute_product_sql_database(substitution, None)

                if product_id != substitution_id:
                    sql = "INSERT INTO product_substitute_product (product_id_1, product_id_2) " \
                          "VALUES (%s, %s) " \
                          "ON DUPLICATE KEY UPDATE product_id_2 = product_id_2;"
                    val = (product_id, substitution_id)

                    self.cursor.execute(sql, val)

        sql = "UPDATE product SET research_substitutes = %s WHERE id = %s"
        val = (1, product_id)
        self.cursor.execute(sql, val)

        self.mydb.commit()

    def close(self):
        self.cursor.close()
        self.mydb.close()
