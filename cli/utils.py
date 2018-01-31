#!/usr/bin/env python3

def choice(message, default=False):
    yes = ['y', 'Y', 'yes', 'Yes']
    no = ['n', 'N', 'no', 'No', '']

    if default:
        yes.append('')
        msg = '{} [Y/n]: '
    else:
        no.append('')
        msg = '{} [y/N]: '
    result = input(msg.format(message))
    if result in yes:
        return True
    elif result in no:
        return False
    else:
        return None
