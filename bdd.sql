USE openfoodfacts;


create table ingredient (
	id smallint unsigned auto_increment,
	name varchar(150) not null,
    unique index ind_un_ingredient_name (name),
	PRIMARY KEY(id)
);


CREATE TABLE product_ingredient (
	ingredient_id smallint unsigned,
	product_id smallint unsigned,
	PRIMARY KEY (ingredient_id, product_id)
);


create table store (
	id smallint unsigned auto_increment,
	name varchar(150) not null,
    unique index ind_un_store_name (name),
	PRIMARY KEY(id)
);


CREATE TABLE product_store (
	store_id smallint unsigned,
	product_id smallint unsigned,
	PRIMARY KEY (store_id, product_id)
);


create table brand (
	id smallint unsigned auto_increment,
	name varchar(150) not null,
    unique index ind_uni_brand_name (name),
	PRIMARY KEY(id)
);


CREATE TABLE product_brand (
	brand_id smallint unsigned,
	product_id smallint unsigned,
	PRIMARY KEY (brand_id, product_id)
);


CREATE TABLE category (
	id smallint unsigned auto_increment,
	name varchar(150) not null,
    unique index ind_uni_category_name (name),
	PRIMARY KEY(id)
);


CREATE TABLE product_category (
	category_id smallint unsigned,
	product_id smallint unsigned,
	PRIMARY KEY (category_id, product_id)
);


create table product (
	id smallint unsigned not null auto_increment,
    product_name varchar(255) not null,
    generic_name varchar(255) not null,
    nutrition_grades varchar(1) not null,
	bar_code_unique varchar(50) not null,
    research_substitutes boolean not null default 0,
    unique index ind_uni_bar_code_unique (bar_code_unique),
    primary key (id)
);


create table product_substitute_product (
	product_id_1 smallint unsigned,
    product_id_2 smallint unsigned,
    primary key (product_id_1, product_id_2)
);


alter table product_category
add constraint fk_category_product_category_id foreign key (category_id) references category(id),
add constraint fk_category_product_product_id foreign key (product_id) references product(id);


alter table product_ingredient
add constraint fk_product_ingredient_ingredient_id foreign key (ingredient_id) references ingredient(id),
add constraint ffk_product_ingredient_product_id foreign key (product_id) references product(id);


alter table product_brand
add constraint fk_product_brand_brand_id foreign key (brand_id) references brand(id),
add constraint ffk_product_brand_product_id foreign key (product_id) references product(id);


alter table product_substitute_product
add constraint fk_product_substitute_product_product_id_1 foreign key (product_id_1) references product(id),
add constraint ffk_product_substitute_product_product_id_2 foreign key (product_id_2) references product(id);


alter table product_store
add constraint fk_product_store_store_id foreign key (store_id) references store(id),
add constraint ffk_product_store_product_id foreign key (product_id) references product(id);


DELIMITER |
create procedure check_if_product_exist_by_bar_code(in p_code_bar varchar(50), out p_product_id smallint unsigned, out p_exist_substitutes boolean, out p_research_subsitutes boolean)
begin
	DECLARE EXIT HANDLER FOR NOT FOUND
    begin
		set p_product_id = 0;
        set p_exist_substitutes = 0;
		set p_research_subsitutes = 0;
    end;

	select product.id,
			  case
			  when group_concat(product_substitute_product.product_id_2) is null then 0
			  else 1
              end,
              product.research_substitutes
			  into p_product_id, p_exist_substitutes, p_research_subsitutes
    from product
    
    left join product_substitute_product on  product.id = product_substitute_product.product_id_1
    
    where product.bar_code_unique = p_code_bar
    group by product.id;
end|
DELIMITER ;

DELIMITER |
CREATE PROCEDURE get_product_detail(in p_product_id smallint unsigned)
BEGIN
	select product.product_name as product_name,
			  product.generic_name as generic_name,
			  product.nutrition_grades as nutrition_grades,
              product.bar_code_unique as code,
              group_concat(distinct store.name separator ', ') as stores_tags,
			  group_concat(distinct category.name separator ', ') as categories,
			  group_concat(distinct ingredient.name separator ', ') as ingredients,
			  group_concat(distinct brand.name separator ', ') as brands_tags,
              group_concat(distinct product_substitute_product.product_id_2) as substitutes
	from product
	
	left join product_category on product.id = product_category.product_id
	left join category on product_category.category_id = category.id
	
	left join product_ingredient on product.id = product_ingredient.product_id
	left join ingredient on product_ingredient.ingredient_id = ingredient.id
    
	left join product_brand on product.id = product_brand.product_id
	left join brand on product_brand.brand_id = brand.id

	left join product_store on product.id = product_store.product_id
	left join store on product_store.store_id = store.id
	
	left join product_substitute_product on  product.id = product_substitute_product.product_id_1
	
	where product.id = p_product_id
	group by product.id;
end|
DELIMITER ;

create or replace view V_get_substitutable_products
as select product.id, 
			  product.product_name,
			  product.generic_name,
              product.bar_code_unique as code,
			  case
			  when group_concat(product_substitute_product.product_id_2) is null then 0
			  else 1
              end as substitutes_exist,
              product.research_substitutes
    from product
    left join product_substitute_product on  product.id = product_substitute_product.product_id_1
    where product.research_substitutes = 1
    group by product.id
    having substitutes_exist = 1;
