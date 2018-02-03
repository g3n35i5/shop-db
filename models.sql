CREATE TABLE consumers (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	active BOOLEAN NOT NULL,
	karma INTEGER NOT NULL,
	credit INTEGER NOT NULL,
	email VARCHAR(64),
	password BLOB(256),
	studentnumber INTEGER,
	PRIMARY KEY (id),
	UNIQUE (name),
	CHECK (active IN (0, 1)),
	CHECK (karma BETWEEN -10 AND 10)
);

CREATE TABLE departments (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	income_base INTEGER NOT NULL,
	income_karma INTEGER NOT NULL,
	expenses INTEGER NOT NULL,
	budget INTEGER NOT NULL,
	PRIMARY KEY (id)
);


CREATE TABLE pricecategories (
	id INTEGER NOT NULL,
	price_lower_bound INTEGER NOT NULL,
	additional_percent INTEGER NOT NULL,
	PRIMARY KEY (id),
	CHECK (price_lower_bound >= 0),
	CHECK (additional_percent >=0)
);

CREATE TABLE products (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	barcode VARCHAR(24),
	price INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	stock INTEGER,
	countable BOOLEAN NOT NULL,
	revocable BOOLEAN NOT NULL,
	image VARCHAR(64) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	FOREIGN KEY(department_id) REFERENCES departments (id),
	CHECK (active IN (0, 1)),
	CHECK (revocable IN (0, 1)),
	CHECK (countable IN (0, 1))
);

CREATE TABLE purchases (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	revoked BOOLEAN NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	paid_base_price_per_product INTEGER NOT NULL,
	paid_karma_per_product INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumers (id),
	FOREIGN KEY(product_id) REFERENCES products (id),
	CHECK (revoked IN (0, 1))
);

CREATE TABLE deposits (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumers (id)
);

CREATE TABLE payoffs (
	id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	amount INTEGER NOT NULL,
	revoked BOOLEAN NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (department_id) REFERENCES departments (id),
	CHECK (revoked IN (0, 1))
);

CREATE TABLE logs (
	id INTEGER NOT NULL,
	table_name VARCHAR(64) NOT NULL,
	updated_id INTEGER NOT NULL,
	data_inserted VARCHAR(256) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE stockhistory (
	id INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	new_stock INTEGER NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE banks (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	credit INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE adminroles (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (consumer_id) REFERENCES consumers (id),
	FOREIGN KEY (department_id) REFERENCES departments (id)
);

CREATE TABLE workactivities (
	id INTEGER NOT NULL,
	name VARCHAR(32) NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE activities (
	id INTEGER NOT NULL,
	created_by INTEGER NOT NULL,
	workactivity_id INTEGER NOT NULL,
	date_created TIMESTAMP NOT NULL,
	date_deadline TIMESTAMP NOT NULL,
	date_event TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (created_by) REFERENCES consumers (id),
	FOREIGN KEY (workactivity_id) REFERENCES workactivities (id)
);

CREATE TABLE activityfeedbacks (
	id INTEGER NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	consumer_id INTEGER NOT NULL,
	activity_id INTEGER NOT NULL,
	feedback BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (consumer_id) REFERENCES consumers (id),
	FOREIGN KEY (activity_id) REFERENCES activities (id)
);
INSERT INTO banks (name, credit) VALUES ("Hauptkonto", 0);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (0, 60);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (10, 50);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (20, 40);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (50, 30);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (80, 25);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (100, 20);
INSERT INTO pricecategories (price_lower_bound, additional_percent) VALUES (200, 15);
