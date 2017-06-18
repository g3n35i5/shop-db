# shop.db
This is the documentation for shop.db.

Table of content
1. [About shop.db](#about-shopdb)
2. [Usage](#usage)
3. [Database schema](#database-schema)
4. [Models](#models)
5. [Validatable objects](#validatable-objects)
5. [The karma system](#the-karma-system)
6. [shop.db API](#shopdb-api)
7. [shop.db internal functions](#shopdb-internal-functions)


### About shop.db

We created shop.db in order to offer a simple way to manage purchases and
consumer interactions in a small community. Over time, the project grew bigger
and bigger and we decided to make it as flexible as possible, so that i can be
used for more applications than our small shop service. Even if the development
of shop.db has not progressed far enough to be called finished, we want to
share the project so anyone can contribute and make shop.db better. In the
following part, you can find a basic documentation for this project.


### Usage

shop.db can be used as a standalone backend and can be accessed via it's API.
Because this is not an elegant way to use this application, we developed the
shop.db frontend, which can be found in it's own repository.


## Database schema

shop.db does not use any common sql database toolkit (e.g. sqalchemy), but a
self-written api. The documentation for this api can be found in the next
chapter. This chapter focuses on the different tables in shop.db.
Some of these tables are absolutely necessary for shop.db, others are optional.
A complete overview can be found in models.txt located in the documentation
folder of this project.

#### Important tables
- consumers
- products
- departments
- deposits
- purchases
- payoffs
- bank
- information
- karmascale
- logs

#### Optional tables
- deeds
- participations
- flags

## Models

For each table, there is a Model defined as python Class. These models are
defined as python classes in the file models.py, which can be found in the
backend folder. Keep in mind, that all these models are a so-called ValidatableObject, which gets explained in the after this paragraph.

#### Consumer

| Key    | Type                   | Description           |
|--------|------------------------|-----------------------|
| id     | integer                | unique identifier     |
| name   | string, 4 to 64 chars  | name of the consumer  |
| karma  | integer, -10 to 10     | karma of the consumer |
| active | boolean                | state of the consumer |

To create a consumer in python, you can use this snippet
```python
name = "John Doe"
credit = 200
karma = 5
active = True
c = Consumer(name=name, credit=credit, karma=karma, active=active)
```


## Validatable objects
TODO

## The karma system

Unfortunately, even in the best community there are products go missing over
the time. In order to compensate this loss, we decided to implement the
so-called karma system. Each consumer gets a karma value ranged from -10 to 10.
This karma value defines, how much this consumer has to pay in addition to the
base cost of a product.

The table "pricecategories" contains an incremental
percental addition, based on the cost of a product. Below, you see an example
for a possible pricecategory distribution.

| id  | price_lower_bound | additional_percent |
|-----|-------------------|--------------------|
|  1  |         10        |        50          |
|  2  |         20        |        40          |
|  3  |         50        |        30          |
|  4  |         80        |        25          |
|  5  |         100       |        20          |
|  6  |         200       |        15          |

Let's say, the consumer, who has a karma of 5, buys a product which costs 40
cents.
```python
base_price = 40
karma = 5
percent = 40 # You can get this value by looking at the table above
price = floor(base_price * (1 + percent * (-karma + 10) / 2000))

# The price the consumer has to pay results in 44 cents
```
As it turned out, this karma system compensates the loss and appeared as the
fairest solution for all consumer to us.

## shop.db API

All requests to shop.db are processed by the shop.db webapi. It's a simple
flask application handling all http requests and passes them to the shop.db
backend. We use flask app routes to process the requests, here is a list of
all routes.

#### Backing up the database via http request
```python
@app.route('/backup', methods=['POST'])
```

#### Handling consumers
```python
# List all consumers
@app.route('/consumers', methods=['GET'])

# Insert consumer
@app.route('/consumers', methods=['POST'])

# Get consumer by id
@app.route('/consumer/<int:id>', methods=['GET'])

# Update consumer
@app.route('/consumers/<int:id>', methods=['PUT'])

# Get all purchases of one consumer
@app.route('/consumer/<int:id>/purchases', methods=['GET'])

# Get all deposits of one consumer
@app.route('/consumer/<int:id>/deposits', methods=['GET'])

# List the favorite products of one consumer
@app.route('/favorites/<int:id>', methods=['GET'])

# List the karma history of one consumer
@app.route('/karmahistory/<int:id>', methods=['GET'])
```

#### Handling products
```python
# List all products
@app.route('/products', methods=['GET'])

# Insert product
@app.route('/products', methods=['POST'])

# Get product by id
@app.route('/product/<int:id>', methods=['GET'])

# Update product
@app.route('/products/<int:id>', methods=['PUT'])
```

#### Handling purchases
```python
# List all purchases
@app.route('/purchases', methods=['GET'])

# List the latest purchases with a variable limit
@app.route('/purchases/<int:limit>', methods=['GET'])

# Insert purchase
@app.route('/purchases', methods=['POST'])

# Get purchase by id
@app.route('/purchase/<int:id>', methods=['GET'])

# Update purchase
@app.route('/purchases/<int:id>', methods=['PUT'])
```

#### Handling deposits
```python
# List all deposits
@app.route('/deposits', methods=['GET'])

# List the latest deposits with a variable limit
@app.route('/deposits/<int:limit>', methods=['GET'])

# Insert deposit
@app.route('/deposits', methods=['POST'])
```

#### Handling pricecategories
```python
# List the pricecategories
@app.route('/pricecategories', methods=['GET'])
```

#### Handling backend database scheme information
```python
# Get information about the database scheme
@app.route('/information', methods=['GET'])
```

## shop.db internal functions
In this paragraph, you will find all necessary functions in the shop.db
backend. These functions are accessed by the shop.db API, but can be included
in any other application as well. Functions which start with an underscore
are private functions and should NOT be called externally.

TODO
