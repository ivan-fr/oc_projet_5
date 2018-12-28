DB_HOST = 'localhost'
DB_USER = 'root'
DB_NAME = 'openfoodfacts'
DB_PWD = 'hWfY7Uv82k7L9f2Sr._.'

STORE_DEPARTMENT = {
    'Prêt à deguster': ('Sandwichs', 'Desserts', 'Entrées'),
    'Fruits et Légumes': ('Fruits', 'Légumes frais'),
    'Viande et Poissons': ({
        'boucherie': (
            'Viandes fraîches', 'Bœuf', 'Viandes de veau', 'Porc'),
        'Poissonnerie': ('Fruits de mer', 'Sushi')
    }),
    'Pains et Pâtisseries': ('Pain', 'Gâteaux'),
    'Crémerie': ('Œufs', 'Crèmes fraîches', 'Laits', 'Boissons lactées',
                 {
                     'Fromages': (
                         'Raclettes', 'Camemberts', 'Coulommiers', 'Bries',
                         'Roqueforts', 'Fromages de brebis',
                         'Mozzarella', 'Feta', 'Emmentals', 'Comté',
                         'Cantal', 'Fromages en tranches',
                         'Fromages râpés'),
                     'Yaourts, desserts et spécialités végétales': (
                         'Fromages blancs', 'Yaourts natures',
                         'Yaourts aux fruits',
                         'Fromages blancs aux fruits',
                         'Yaourts à boire', 'Mousses sucrées',
                         'Yaourts au Bifidus'),
                     'Beurres et margarines': (
                         'Beurres doux', 'Beurres demi-sel', 'Margarines')
                 }),
    'Charcuterie': (
        'Foies gras', 'Jambons blancs', 'Rôtis de porc', 'Saucissons',
        'Chorizos',
        'Lardons de porc', 'Knacks industrielles', 'Saucisses', 'boudins'),
    'Epicerie Salée': ({
                           "Pour l'apéritif": (
                               'Chips', 'Cacahuètes', 'Olives',
                               'Tuiles salées',
                               'Tortillas', 'Biscuits apéritifs',
                               'Pistaches'),
                           'Soupes et croutons': (
                               'Soupes', 'Soupes déshydratées', 'Croûtons'),
                           'Les Plats cuisinés': (
                               'Raviolis au bœuf', 'Couscous préparés',
                               'Taboulés',
                               'Cassoulets', 'Confits de canard',
                               'Choucroutes'),
                           'Conserves et bocaux': (
                               'Maïs', 'Asperges',
                               'Macédoines de légumes en conserve',
                               'Ratatouilles',
                               'Champignons en conserve',
                               'Tomates en conserve', 'Thons en conserve',
                               'Sardines en conserve'),
                           'Huiles, vinaigres, condiments et sauces': (
                               "Huiles d'olive", "Huiles de tournesol",
                               "Vinaigres",
                               "Vinaigrettes", "Jus de citron",
                               "Cornichons",
                               "Olives", "Moutardes", "Ketchup",
                               "Mayonnaises"),
                           'Sel, épices et bouillons': (
                               'Sels', 'Poivres', 'Epices',
                               'Herbes aromatiques', 'Bouillons')
                       }, 'Pâtes alimentaires', 'Riz'),
    'Epicerie Sucrée': ('Bonbons', 'Confiseries chocolatées', 'Confiseries',
                        'Céréales pour petit-déjeuner',
                        'Barres de céréales', 'Pains de mie', 'Confitures',
                        'Pâtes à tartiner', 'Biscuits',
                        {
                            'Compotes, fruits au sirop et crèmes desserts':
                                ('Compotes', 'Fruits au sirop',
                                 'Crèmes dessert'),
                            'Sucres, farines': (
                                'Sucres', 'Farines'),
                            'Diététique': (
                                'Produits sans gluten', 'Boissons sucrées',
                                'Thés')
                        }),
    'Surgelés': ('Pizzas', 'Pizzas et tartes surgelées', 'Frites surgelées',
                 {'Glaces et sorbets': (
                     'Crèmes glacées', 'Bâtonnets glacés',
                     'Cônes', 'Bûches glacées', 'Glaces et sorbets')})
}
