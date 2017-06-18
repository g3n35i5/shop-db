## information:

- id: int
- version_major: int
- version_minor: int


## consumers

- id: int
- credit: int
- karma: int between -10 and 10
- name: varchar[64]
- active: bool


## departments

- id: int
- name: varchar[64]
- income_base: int
- income_karma: int
- expenses: int
- budget: int


## karmascale

- id: int
- price_bound: int
- additional_percent: int


## products

- id: int
- name: varchar[64]
- barcode: varchar[24]
- price: int
- department_id: int : foreignkey
- active: bool
- on_stock: bool
- revocable: bool
- image: varchar[64]


## purchases

- id: int
- consumer_id: int : foreignkey
- product_id: int : foreignkey
- amount: int
- comment: varchar[64]
- timestamp: timestamp
- revoked: bool
- paid_price_per_product: int


## deposits

- id: int
- consumer_id: int : foreignkey
- amount: int
- comment: varchar[64]
- timestamp: timestamp


## payoffs

- id: int
- bank_id: int : foreignkey
- department_id: int : foreignkey
- comment: varchar[64]
- amount: int
- timestamp: timestamp


## logs

- id: int
- table_name: varchar[64]
- updated_id: int
- data_inserted: varchar[256]
- timestamp: timestamp


## deeds

- id: int
- name: varchar[64]
- timestamp: timestamp
- done: bool


## participations

- id: int
- deed_id: int : foreignkey
- consumer_id: int : foreignkey
- flag_id: int : foreignkey
- timestamp timestamp


## flags

- id: int
- name: varchar[64]

## banks

- id: int
- name: varchar[64]
- credit: int
