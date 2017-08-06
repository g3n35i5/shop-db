## Changelog

### Version 3.0
- Products now have an image name

### Version 3.1
- Intoducing changelog
- The database has now its own table "information" to store relevant information in order to
  work together with the frontend.
- Under certain conditions it was technically possible to revoke a purchase
  twice. This Bug is fixed now.
- Inserting the current payoffs of the departments "Kaffeewart" and
  "Süßigkeitenwart"

### Version 3.2
- Adding Pizzawart

### Version 3.3

+ Adding Barcodes

### Version 3.4

+ Adding department "Getränkewart"


### Version 3.5

- Changes in products:
  - **on_stock** is deprecated and removed 
  - **countable** is a new field which marks wether a product gets counted with every purchase or not.
  - **stock** integer which is counted down with every purchase (if countable is true).


### Version 3.6

+ Resetting department payoffs to 0, because that payoffs were directly written to the database without the use of the api.