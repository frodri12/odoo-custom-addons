#

from random import randint

def generate_random_code( moveId):
    pin_length = 9
    number_max = (10**pin_length) - 1
    number = randint( 0, number_max)
    delta = (pin_length - len(str(number))) * '0'
    random_code = '%s%s' % (delta,number)
    condition = _validate_random_code( moveId, random_code)
    if condition:
        generate_random_code(moveId)
    moveId.l10n_py_dnit_ws_random_code = random_code
    return random_code

def _validate_random_code( moveId, code):
    acc = moveId.env['account.move'].search([('l10n_py_dnit_ws_random_code', '=', code)])
    if len(acc) > 0:
        return True
    else:
        return False
