CREATE TABLE consumer (
	id INTEGER NOT NULL,
	name VARCHAR(128) NOT NULL,
	active BOOLEAN NOT NULL,
	credit INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	CHECK (active IN (0, 1))
);

CREATE TABLE product (
	id INTEGER NOT NULL,
	name VARCHAR(128) NOT NULL,
	price INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	on_stock BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	CHECK (active IN (0, 1)),
	CHECK (on_stock IN (0, 1))
);

CREATE TABLE purchase (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	revoked BOOLEAN NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	paid_price_per_product INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumer (id),
	FOREIGN KEY(product_id) REFERENCES product (id),
	CHECK (revoked IN (0, 1))
);

CREATE TABLE deposit (
	id INTEGER NOT NULL,
	consumer_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	comment VARCHAR(128) NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(consumer_id) REFERENCES consumer (id)
);
