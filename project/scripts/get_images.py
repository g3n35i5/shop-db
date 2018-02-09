#!/usr/bin/python3

import argparse
import os.path
import shutil
import sys

import requests


def get_image_name(url):
    url = url.split('/')
    return url[4]


def get_image(url):
    r = requests.get(url + '?resize=150px:150px', stream=True)
    if r.status_code == 200:
        return r.raw
    return None


def save_image(path, data):
    if data is not None:
        with open(path, 'wb') as f:
            data.decode_content = True
            shutil.copyfileobj(data, f)
    else:
        print("could not save image because no data was given")


def main():
    parser = argparse.ArgumentParser(description='Insert products to shop.db')
    parser.add_argument('-f', '--file', help='text file with image urls',
                        default=None)
    args = vars(parser.parse_args())

    if args['file'] is not None:
        if not os.path.exists(args['file']):
            sys.exit("{} does not exists".format(args['file']))

        with open(args['file']) as _file:
            data = _file.readlines()
            for url in data:
                url = url.strip()
                name = get_image_name(url)
                data = get_image(url)
                save_image("./images/{}".format(name), data)


if __name__ == "__main__":
    main()
