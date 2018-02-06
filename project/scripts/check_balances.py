#!/usr/bin/python3

# This script takes all purchases and deposits and sums their
# amount for each user. So at least, this value should be
# equal to the actual balance of the user, if there was no
# initial_balane for the consumer.
#
# initial_balance is highly undesirable, since there does not
# exist a way (besides calculating it backwards) to see this
# initial_balance. The only way to calculate it, is this script.
#
# So use this script to ensure, there was no calculation mistake!
# (which is the case, if all initial_balance values are 0)

# This script won't change anything on the running instance!
# It just does some GET requests.

from operator import itemgetter

import requests

server = 'http://shop.gatrobe.de:5000/'

if not server.endswith('/'):
    server += '/'


def get_consumers():
    return requests.get(server + 'consumers').json()


def get_consumer(cid):
    return requests.get(server + 'consumer/' + str(cid)).json()


def get_purchases(cid):
    purchases = requests.get(server + 'consumer/' +
                             str(cid) + '/purchases').json()
    pur = []

    for purchase in purchases:
        if not purchase['revoked']:
            pur.append(purchase)

    return pur


def get_deposits(cid):
    return requests.get(server + 'consumer/' + str(cid) + '/deposits').json()


def calc_theoretical_amount(cid):
    purchases = get_purchases(cid)
    deposits = get_deposits(cid)

    d_amount = sum(map(itemgetter('amount'), deposits))
    p_amount = - \
        sum(map(lambda x: x['paid_base_price_per_product']
                * x['amount'], purchases))
    k_amount = - \
        sum(map(lambda x: x['paid_karma_per_product']
                * x['amount'], purchases))

    return [d_amount, p_amount, k_amount]


def actual_amount(cid):
    return get_consumer(cid)['credit']


if __name__ == '__main__':
    consumers = get_consumers()

    print('{:25} {:>10} {:>10} {:>20}'.format(
        'NAME', 'theoretical', 'actual', 'initial_balance'))
    print()

    for consumer in consumers:
        theoretical = sum(calc_theoretical_amount(consumer['id'])) / 100
        actual = actual_amount(consumer['id']) / 100

        initial_balance = actual - theoretical

        print('{:25} {:10.2f} {:10.2f} {:20.2f}'.format(
            consumer['name'], theoretical, actual, initial_balance))
