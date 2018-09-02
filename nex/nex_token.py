"""
NEX Token Settings
===================================

Author: Thomas Saunders
Email: tom@neonexchange.org

Date: Aug 31 2018

"""

from boa.interop.Neo.Storage import *
from boa.interop.Neo.Runtime import CheckWitness, GetTime
from boa.builtins import concat

TOKEN_NAME = 'NEX Token'

TOKEN_SYMBOL = 'NEX'

TOKEN_DECIMALS = 8

TOKEN_OWNER1 = b'P}\xd1\xf0\x0e0\xe7\x95Z\xb8\xb3Ip\x7fB\xfa+e7k'
TOKEN_OWNER2 = b'Q\xb8$\xa5f\xa6ECu\x9c\xd5\xc9X\xc1\x93\xaf\xa4\xd0\xb8\xfb'
TOKEN_OWNER3 = b'\x99>:\x81\x00-KZV\xac\x98\x08\xce\xec\x1f\xef\xcb.\xbc\xf5'
TOKEN_OWNER4 = b'\xed\xcf\xa8\x03Vl\x06\x00\xa6\x82\xd6\xc8\x9a\xb4\xd05\xe13F\xba'
TOKEN_OWNER5 = b'\xe3\x9cZ\x9e\x04u\x1b\xfb\x85\xdf\xd0\xb6\x07vl\xdc\xb9\x95q\x9f'

TOKEN_CIRC_KEY = b'in_circulation'

TOKEN_TOTAL_SUPPLY = 50000000 * 100000000  # 50m total supply * 10^8 ( decimals)

TOKEN_INITIAL_AMOUNT = 15000000 * 100000000  # 15m to start * 10^8

OWNER_LOCK_TOTAL = 10000000 * 100000000  # 10m total for all owners * 10^8
PER_OWNER_TOTAL = 2000000 * 100000000  # 2m total for each owner * 10^8

# 1 dollar per token, and one neo = 18.54 dollars * 10^8 (10 day SMA Aug 30 2018)
TOKENS_PER_NEO = 1854 * 1000000  # 1,854,000,000

# one gas = 5.93 dollars * 10^8  (10 day SMA Aug 30 2018)
TOKENS_PER_GAS = 593 * 1000000  # 593,000,000

# maximum amount you can mint in round 1 (1000 * 10^8 )
MAX_EXCHANGE_ROUND1 = 1000 * 100000000
MAX_EXCHANGE_ROUND2 = 9000 * 100000000

# when to start the crowdsale
ROUND1_START = 1535997600  # Sept 3 2018, 1800 UTC
ROUND1_END = 1536343200  # Sept 7 2018, 1800 UTC
ROUND2_START = 1536602400  # Sept 10 2018, 1800 UTC
ROUND2_END = 1536948000  # Sept 14 2018, 1800 UTC

MINTED_ROUND1_KEY = b'mintedR1'
MINTED_ROUND2_KEY = b'mintedR2'


PREFIX_BALANCE = b'balance'
PREFIX_ALLOWANCE = b'allowance'


def crowdsale_available_amount(ctx):
    """

    :return: int The amount of tokens left for sale in the crowdsale
    """

    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    available = TOKEN_TOTAL_SUPPLY - in_circ

    return available


def add_to_circulation(ctx, amount):
    """
    Adds an amount of token to circlulation

    :param amount: int the amount to add to circulation
    """

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def get_circulation(ctx):
    """
    Get the total amount of tokens in circulation

    :return:
        int: Total amount in circulation
    """
    return Get(ctx, TOKEN_CIRC_KEY)


def get_balance_key(addr):

    return concat(PREFIX_BALANCE, addr)

def get_allowance_key(addr1, addr2):

    return concat(PREFIX_ALLOWANCE, concat(addr1, addr2))
