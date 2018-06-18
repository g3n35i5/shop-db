DROP TABLE departmentpurchases;
DELETE FROM payoffs WHERE departmentpurchase_id NOT NULL;

CREATE TABLE IF NOT EXISTS departmentpurchasecollections (
	id INTEGER NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	comment VARCHAR(64),
	department_id INTEGER NOT NULL,
	admin_id INTEGER NOT NULL,
	revoked BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(department_id) REFERENCES departments (id),
	FOREIGN KEY(admin_id) REFERENCES consumers (id),
	CHECK (revoked IN (0, 1))
);

CREATE TABLE IF NOT EXISTS departmentpurchases (
	id INTEGER NOT NULL,
	collection_id INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	total_price INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (collection_id) REFERENCES departmentpurchasecollections (id),
	FOREIGN KEY (product_id) REFERENCES products (id)
);

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS payoffs_bak (
	id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	admin_id INTEGER NOT NULL,
	comment VARCHAR(64) NOT NULL,
	amount INTEGER NOT NULL,
	revoked BOOLEAN NOT NULL,
	timestamp TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (department_id) REFERENCES departments (id),
	FOREIGN KEY (admin_id) REFERENCES consumers (id),
	CHECK (revoked IN (0, 1))
);

INSERT INTO payoffs_bak SELECT
id,
department_id,
30,
comment,
amount,
revoked,
timestamp
FROM payoffs;
DROP TABLE payoffs;
ALTER TABLE payoffs_bak RENAME TO payoffs;
COMMIT;
