from sqlalchemy import *

db = create_engine('sqlite:///shop.db')

db.echo = True  # Try changing this to True and see what happens

metadata = BoundMetaData(db)

customers = Table('customers', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('name', String(40)),
    Column('age', Integer),
    Column('password', String),
)
customers.create()

i = customers.insert()
i.execute(name='Mary', age=30, password='secret')
i.execute({'name': 'John', 'age': 42},
          {'name': 'Susan', 'age': 57},
          {'name': 'Carl', 'age': 33})

s = customers.select()
rs = s.execute()

row = rs.fetchone()
print 'Id:', row[0]
print 'Name:', row['name']
print 'Age:', row.age
print 'Password:', row[customers.c.password]

for row in rs:
    print row.name, 'is', row.age, 'years old'
