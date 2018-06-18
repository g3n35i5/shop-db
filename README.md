# shop-db
This is the documentation for shop.db.

## Table of content

1.  [About shop.db](#about-shopdb)
2.  [Dependencies](#dependencies)
3.  [Getting started](#getting-started)
4.  [Backups](#backups)
5.  [Unittests](#unittests)

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

### Dependencies

In order to use shop-db, you need to install the following main dependencies:
  1. Python 3
  2. Python 3 Virtual Environment
  3. pip3
  3. SQLite3
  4. git

```bash
$ sudo apt-get install python3 python3-venv python3-pip sqlite3 git
```

### Getting started

Add an account for shop-db called shopdb_user. Since this account is only for
running shop-db the extra arguments of -rm is added to create a system
account without creating a home directory:

```bash
$ sudo useradd -r shopdb_user
```

Next we will create a directory for the installation of shop-db and change
the owner to the shopdb_user account:

```bash
$ cd /srv
$ sudo git clone https://github.com/g3n35i5/shop-db.git
$ sudo chown -R shopdb_user:shopdb_user shop-db
```

Next up is to create and change to a virtual environment for shop-db. This
will be done as the shopdb_user account:
```bash
$ sudo su -s /bin/bash shopdb_user
$ cd /srv/shop-db
$ python3 -m venv .
$ source bin/activate
```

Now the configuration file of shop-db has to be adjusted. The most important
change is the SECRET_KEY. This is later responsible for salting the user
passwords and must be kept secret under all circumstances. Change this
SECRET_KEY in the file `project/configuration.py`. You can do this with a
normal text editor or with the command `sed`:

```bash
(shop-db) $ sed -i 's/supersecretkey/YOURBETTERSUPERSECRETKEY/g' project/configuration.py
```

Once you have activated the virtual environment you will notice the prompt
change and then you can setup shop-db:

```bash
(shop-db) $ pip3 install -r requirements.txt
(shop-db) $ ./setup.py
```

Now that the installation is complete, we can move on. In order for shop-db to
work, at least one consumer and department must be created. It is recommended
that you define an administrator directly. In order for a consumer to become an
administrator, he/she must have provided access data, i. e. email address and
password:

```bash
(shop-db) $ ./manager.py add consumer
(shop-db) $ ./manager.py add department
(shop-db) $ ./manager.py admin add
```

Ready. Almost. To start the Webapi and use the shop-db backend, you only have to
start the webapi:

```bash
(shop-db) $ ./shopdb.py
```

However, so that the backend does not have to be started manually every time, it
is advisable to run shop-db as a systemd service:

```bash
(shop-db) $ exit # To switch back to the root user
$ sudo nano /etc/systemd/system/shop-db@shopdb_user.service
```

The file must have the following content:

```
[Unit]
Description=shop-db
After=network-online.target

[Service]
Type=simple
User=%i
ExecStart=/srv/shop-db/bin/python3 /srv/shop-db/shopdb.py

[Install]
WantedBy=multi-user.target
```

You need to reload systemd to make the daemon aware of the new configuration:

```bash
$ sudo systemctl --system daemon-reload
```

To have shop-db start automatically at boot, enable the service:

```bash
$ sudo systemctl enable shop-db@shopdb_user
```

To disable the automatic start, use this command:

```bash
$ sudo systemctl disable shop-db@shopdb_user
```

To start shop-db now, use this command:

```bash
$ sudo systemctl start shop-db@shopdb_user
```

### Backups
Backups for shop-db can easily be created with the existing Python script
`backup.py`. The backups are then stored in the shop-db directory according to
the following schema:

```
/srv/shop-db/backups/<year>/<month>/<day>/<hours_minutes_seconds.dump>
```

This script can be executed manually at any time, but it is advisable to create
a cronjob for regular execution. To do this, you can use the command

```bash
$ sudo crontab -e
```

 The advantage of running the cronjob as root user is that the backups belong
to this user and cannot be changed by the shopdb_user. Now the line

```bash
0 */3 * * * /srv/shop-db/backup.py
```

has to be entered in the crontab editor. `0 */3 * * * * *` means that a backup
is performed every day every 3 hours at minute 0, these parameters could be
adapted to individual needs. You can find more information about using crontab
[here](https://help.ubuntu.com/community/CronHowto).


### Unittests
Currently, most of the core features of shop-db are covered with the
corresponding unittests. In order to execute them you can use the command

```bash
$ python -m coverage run test.py
```

If you want to check the test coverage, type

```bash
$ python -m coverage html
```
to generate the html preview and open a webserver in the newly created
directory `htmlcov`

```bash
$ cd htmlcov
$ python -m http.server
```
