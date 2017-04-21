CREATE TABLE consumers (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	active BOOLEAN NOT NULL,
	karma INTEGER NOT NULL,
	credit INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	CHECK (active IN (0, 1)),
	CHECK (karma BETWEEN -10 AND 10)
);

CREATE TABLE departments (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	income INTEGER NOT NULL,
	expenses INTEGER NOT NULL,
	budget INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE products (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	price INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	on_stock BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	FOREIGN KEY(department_id) REFERENCES departments (id),
	CHECK (active IN (0, 1)),
	CHECK (on_stock IN (0, 1))
);

CREATE TABLE purchases (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	revoked BOOLEAN NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	paid_price_per_product INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumer (id),
	FOREIGN KEY(product_id) REFERENCES product (id),
	CHECK (revoked IN (0, 1))
);

CREATE TABLE deposits (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumer (id)
);

CREATE TABLE payoffs (
	id INTEGER NOT NULL,
	bank_id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	amount INTEGER NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (bank_id) REFERENCES bank (id),
	FOREIGN KEY (department_id) REFERENCES departments (id)
);

CREATE TABLE banks (
	id INTEGER NOT NULL,
	name VARCHAR(64) NOT NULL,
	credit INTEGER NOT NULL,
	PRIMARY KEY (id)
);
