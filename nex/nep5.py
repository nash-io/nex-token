from boa.interop.Neo.Runtime import CheckWitness, Notify
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import *
from boa.interop.System.ExecutionEngine import GetExecutingScriptHash, GetCallingScriptHash, GetEntryScriptHash
from boa.builtins import concat

from nex.nex_token import *
from nex.owner import *

OnTransfer = RegisterAction('transfer', 'addr_from', 'addr_to', 'amount')
OnApprove = RegisterAction('approve', 'addr_from', 'addr_to', 'amount')


def handle_nep51(ctx, operation, args, callingScriptHash):

    if operation == 'name':
        return TOKEN_NAME

    elif operation == 'decimals':
        return TOKEN_DECIMALS

    elif operation == 'symbol':
        return TOKEN_SYMBOL

    elif operation == 'totalSupply':
        return TOKEN_TOTAL_SUPPLY

    elif operation == 'balanceOf':
        if len(args) == 1:
            return Get(ctx, get_balance_key(args[0]))

    elif operation == 'transfer':
        if len(args) == 3:
            return do_transfer(ctx, args[0], args[1], args[2], callingScriptHash)

    elif operation == 'transferFrom':
        if len(args) == 3:
            return do_transfer_from(ctx, args[0], args[1], args[2])

    elif operation == 'approve':
        if len(args) == 3:
            return do_approve(ctx, args[0], args[1], args[2], callingScriptHash)

    elif operation == 'allowance':
        if len(args) == 2:
            return do_allowance(ctx, args[0], args[1])

    return False


def do_transfer(ctx, t_from, t_to, amount, callingScriptHash):

    if amount <= 0:
        return False

    if len(t_to) != 20:
        return False

    # if the calling script hash is not the entry script hash
    # we force the `t_from` to be the address of the callingScriptHash
    if callingScriptHash != GetEntryScriptHash():
        print("Cannot call from another contract on behalf of other addresses")
        print("Setting from address to callingScriptHash")
        t_from = callingScriptHash
    else:
        if t_from == GetExecutingScriptHash():

            if not check_owners(ctx, 3):
                print("Must authenticate as owners")
                return False

        else:
            if not CheckWitness(t_from):
                print("Insufficient priveleges")
                return False

    from_balance_key = get_balance_key(t_from)
    to_balance_key = get_balance_key(t_to)

    from_balance = Get(ctx, from_balance_key)

    if from_balance < amount:
        Notify("insufficient funds")
        return False

    if t_from == t_to:
        return True

    if from_balance == amount:
        Delete(ctx, from_balance_key)

    else:
        difference = from_balance - amount
        Put(ctx, from_balance_key, difference)

    to_balance = Get(ctx, to_balance_key)

    to_total = to_balance + amount

    Put(ctx, to_balance_key, to_total)

    OnTransfer(t_from, t_to, amount)

    return True


def do_transfer_from(ctx, t_from, t_to, amount):

    if amount <= 0:
        return False

    available_key = get_allowance_key(t_from, t_to)

    # addr1 + addr2 + len(allowance)
    if len(available_key) != 49:
        return False

    available_balance = Get(ctx, available_key)

    if available_balance < amount:
        Notify("Insufficient funds approved")
        return False

    from_balance_key = get_balance_key(t_from)
    to_balance_key = get_balance_key(t_to)

    from_balance = Get(ctx, from_balance_key)

    if from_balance < amount:
        Notify("Insufficient tokens in from balance")
        return False

    to_balance = Get(ctx, to_balance_key)

    new_from_balance = from_balance - amount

    new_to_balance = to_balance + amount

    Put(ctx, to_balance_key, new_to_balance)
    Put(ctx, from_balance_key, new_from_balance)

    new_allowance = available_balance - amount

    if new_allowance == 0:
        Delete(ctx, available_key)
    else:
        Put(ctx, available_key, new_allowance)

    OnTransfer(t_from, t_to, amount)

    return True


def do_approve(ctx, t_owner, t_spender, amount, callingScriptHash):

    if t_owner == GetExecutingScriptHash():
        print("Cannot approve from contract address. Use transfer")
        return False

    # if the calling script hash is not the entry script hash
    # we force the `t_from` to be the address of the callingScriptHash
    if callingScriptHash != GetEntryScriptHash():
        print("Cannot call from another contract on behalf of other addresses")
        print("Setting from address to callingScriptHash")
        t_owner = callingScriptHash

    else:
        if not CheckWitness(t_owner):
            print("Insufficient priveleges")
            return False

    if len(t_spender) != 20:
        return False

    if amount < 0:
        return False

    # cannot approve an amount that is
    # currently greater than the from balance
    owner_balance_key = get_balance_key(t_owner)

    if Get(ctx, owner_balance_key) >= amount:

        approval_key = get_allowance_key(t_owner, t_spender)

        if amount == 0:
            Delete(ctx, approval_key)
        else:
            Put(ctx, approval_key, amount)

        OnApprove(t_owner, t_spender, amount)

        return True

    print("not enough balance")
    return False


def do_allowance(ctx, t_owner, t_spender):

    return Get(ctx, get_allowance_key(t_owner, t_spender))
