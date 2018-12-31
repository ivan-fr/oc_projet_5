from constants import *
import mysql.connector


class DatabaseManager:
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
        columns = tuple(column[0] for column in self.cursor.description)

        products = []
        for product in fetchall_result:
            products.append(dict(zip(columns, product)))

        return products

    def get_product_detail(self, product_id: int):
        """get product detail from database"""

        self.cursor.callproc('get_product_detail', (product_id,))

        for result in self.cursor.stored_results():
            return dict(zip(result.column_names, result.fetchone()))

    def check_if_product_exist(self, code_product: str):
        """check if product already exist in database"""

        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        return self.cursor.callproc('check_if_product_exist_by_bar_code',
                                    (code_product, 0, 0, 0))

    def fill_list_with_product_and_substitutes(self, product_id: int, list_):
        """Fill a given list with the product and
         his substitutes from the database."""

        list_.append(self.get_product_detail(product_id))

        if list_[0].get('substitutes', ''):
            for substitute_id in str(list_[0].get('substitutes', '')).split(
                    ','):
                list_.append(self.get_product_detail(int(substitute_id)))

    def save_product(self, product: (dict, str), substitutes: (list, None)):
        """Save a product and his substitutes in the database."""

        # procedure_result[1] = p_product_id
        # procedure_result[2] = p_exist_substitutes
        # procedure_result[3] = p_researched_subsitutes
        procedure_result = self.check_if_product_exist(product['code'])

        if procedure_result[1]:
            return procedure_result[1]

        sql = "INSERT INTO product " \
              "(product_name, generic_name," \
              " nutrition_grades, bar_code_unique) " \
              "VALUES (%s, %s, %s, %s);"
        val = (product.get('product_name', ''), product.get('generic_name', ''),
               product.get('nutrition_grades', 'e'), product['code'])

        self.cursor.execute(sql, val)

        r_id = self.cursor.lastrowid

        for category in product.get('categories', ''):
            sql = "INSERT INTO category (name) VALUES (%s) " \
                  "ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (category,)
            self.cursor.execute(sql, val)

            _category_id = self.cursor.lastrowid

            sql = "INSERT INTO product_category (category_id, product_id) " \
                  "VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE category_id = category_id;"
            val = (_category_id, r_id)
            self.cursor.execute(sql, val)

        for ingredient in product.get('ingredients', ''):
            sql = "INSERT INTO ingredient (name) " \
                  "VALUES (%s) " \
                  "ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (ingredient['text'],)
            self.cursor.execute(sql, val)

            _ingredient_id = self.cursor.lastrowid

            sql = "INSERT INTO " \
                  "product_ingredient (ingredient_id, product_id) " \
                  "VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE ingredient_id = ingredient_id;"

            val = (_ingredient_id, r_id)
            self.cursor.execute(sql, val)

        for brand in product.get('brands_tags', ''):
            sql = "INSERT INTO brand (name) " \
                  "VALUES (%s) " \
                  "ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (brand,)
            self.cursor.execute(sql, val)

            _brand_id = self.cursor.lastrowid

            sql = "INSERT INTO product_brand (brand_id, product_id) " \
                  "VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE brand_id = brand_id;"
            val = (_brand_id, r_id)
            self.cursor.execute(sql, val)

        for store in product.get('stores_tags', ''):
            sql = "INSERT INTO store (name) VALUES (%s) " \
                  "ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);"
            val = (store,)
            self.cursor.execute(sql, val)

            _store_id = self.cursor.lastrowid

            sql = "INSERT INTO product_store " \
                  "(store_id, product_id) VALUES (%s, %s) " \
                  "ON DUPLICATE KEY UPDATE store_id = store_id;"
            val = (_store_id, r_id)
            self.cursor.execute(sql, val)

        self.mydb.commit()

        if substitutes is not None:
            self.save_substitutes_sql_database(r_id, substitutes)

        return r_id

    def save_substitutes_sql_database(self, product_id: str, substitutes: list):
        """save relationship beetween products"""

        if substitutes is not None:
            for substitute in substitutes:

                substitution_id = self.save_product(substitute, None)

                if product_id != substitution_id:
                    sql = "INSERT INTO product_substitute_product " \
                          "(product_id_1, product_id_2) " \
                          "VALUES (%s, %s) " \
                          "ON DUPLICATE KEY UPDATE product_id_2 = product_id_2;"
                    val = (product_id, substitution_id)

                    self.cursor.execute(sql, val)

        sql = "UPDATE product SET research_substitutes = %s WHERE id = %s"
        val = (1, product_id)
        self.cursor.execute(sql, val)

        self.mydb.commit()

    def close(self):
        """close the database"""

        self.cursor.close()
        self.mydb.close()
