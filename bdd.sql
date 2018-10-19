USE openfoodfacts;


create table ingredient (
	id smallint unsigned auto_increment,
	nom varchar(150) not null,
    unique index ind_un_ingredient_nom (nom),
	PRIMARY KEY(id)
);


CREATE TABLE produit_ingredient (
	ingredient_id smallint unsigned,
	produit_id smallint unsigned,
	PRIMARY KEY (ingredient_id, produit_id)
);


create table marque (
	id smallint unsigned auto_increment,
	nom varchar(150) not null,
    texte varchar(150) not null,
    unique index ind_uni_marque_nom (nom),
    fulltext index ind_fulltext_marque_texte (texte),
	PRIMARY KEY(id)
);


CREATE TABLE produit_marque (
	marque_id smallint unsigned,
	produit_id smallint unsigned,
	PRIMARY KEY (marque_id, produit_id)
);


CREATE TABLE categorie (
	id smallint unsigned auto_increment,
	nom varchar(150) not null,
    unique index ind_uni_categorie_nom (nom),
	PRIMARY KEY(id)
);


CREATE TABLE produit_categorie (
	categorie_id smallint unsigned,
	produit_id smallint unsigned,
	PRIMARY KEY (categorie_id, produit_id)
);


create table produit (
	id smallint unsigned not null auto_increment,
    nom varchar(255) not null,
    nom_generic varchar(255) not null,
    nutrition_grade varchar(1) not null,
    code_bar varchar(50) not null,
	code_bar_unique varchar(50) not null,
    research_substitutes boolean not null default 0,
    unique index ind_uni_code_bar_unique (code_bar_unique),
    fulltext index ind_fulltext_nom_nom_generic_code_bar (nom, nom_generic, code_bar),
    primary key (id)
);


create table produit_substitute_produit (
	produit_id_1 smallint unsigned,
    produit_id_2 smallint unsigned,
    best smallint not null,
    primary key (produit_id_1, produit_id_2)
);


alter table produit_categorie
add constraint fk_categorie_produit_categorie_id foreign key (categorie_id) references categorie(id),
add constraint fk_categorie_produit_produit_id foreign key (produit_id) references produit(id);


alter table produit_ingredient
add constraint fk_produit_ingredient_ingredient_id foreign key (ingredient_id) references ingredient(id),
add constraint ffk_produit_ingredient_produit_id foreign key (produit_id) references produit(id);


alter table produit_marque
add constraint fk_produit_marque_marque_id foreign key (marque_id) references marque(id),
add constraint ffk_produit_marque_produit_id foreign key (produit_id) references produit(id);


alter table produit_substitute_produit
add constraint fk_produit_substitute_produit_produit_id_1 foreign key (produit_id_1) references produit(id),
add constraint ffk_produit_substitute_produit_produit_id_2 foreign key (produit_id_2) references produit(id);


DELIMITER |
create procedure verifier_si_produit_exist_by_match(in recherche varchar(350),
																   out p_produit_id smallint unsigned,
																   out p_exist_substitutes boolean,
																   out p_research_subsitutes boolean)
begin	
	DECLARE EXIT HANDLER FOR NOT FOUND
    begin
		set p_produit_id = 0;
        set p_exist_substitutes = 0;
		set p_research_subsitutes = 0;
    end;
        
	select produit.id,
			  case
			  when group_concat(produit_substitute_produit.produit_id_2) is null then 0
			  else 1
              end,
              produit.research_substitutes
			  into p_produit_id, p_exist_substitutes, p_research_subsitutes
    from produit
    
	left join produit_marque on produit.id = produit_marque.produit_id
	left join marque on produit_marque.marque_id = marque.id
    
    left join produit_substitute_produit on  produit.id = produit_substitute_produit.produit_id_1
    
    where match(produit.nom, produit.nom_generic, produit.code_bar) against (recherche)
			   or match(marque.texte) against (recherche)
    group by produit.id
    limit 1;
end|
DELIMITER ;

call verifier_si_produit_exist_by_match('3662072013370', @a, @b, @c);
select @a, @b, @c;


DELIMITER |
create procedure verifier_si_produit_exist_by_code_bar(in p_code_bar varchar(50), out p_exist boolean, out p_produit_id smallint unsigned)
begin	
	DECLARE EXIT HANDLER FOR NOT FOUND
    begin
		set p_exist = 0;
    end;
	
    set p_exist = 1;
    
	select produit.id into p_produit_id
    from produit
    where code_bar_unique = p_code_bar;
end|
DELIMITER ;

call verifier_si_produit_exist_by_code_bar('pate à tartiner', @a_, @b_);
select @a_, @b_;


DELIMITER |
CREATE PROCEDURE get_produit_detail(in p_produit_id smallint unsigned)
BEGIN
	select produit.nom as produit_nom,
			  produit.nom_generic as produit_nom_generic,
			  produit.nutrition_grade,
              produit.code_bar,
			  group_concat(distinct categorie.nom separator ', ') as categories,
			  group_concat(distinct ingredient.nom separator ', ') as ingredients,
			  group_concat(distinct marque.nom separator ', ') as marques,
              group_concat(distinct produit_substitute_produit.produit_id_2) as substitutes
	from produit
	
	left join produit_categorie on produit.id = produit_categorie.produit_id
	left join categorie on produit_categorie.categorie_id = categorie.id
	
	left join produit_ingredient on produit.id = produit_ingredient.produit_id
	left join ingredient on produit_ingredient.ingredient_id = ingredient.id
    
	left join produit_marque on produit.id = produit_marque.produit_id
	left join marque on produit_marque.marque_id = marque.id
	
	left join produit_substitute_produit on  produit.id = produit_substitute_produit.produit_id_1
	
	where produit.id = p_produit_id
	group by produit.id;
end|
DELIMITER ;

call get_produit_detail(15)