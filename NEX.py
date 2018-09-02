"""
NEX Token
===================================

Author: Thomas Saunders
Email: tom@neonexchange.org

Date: Aug 31 2018

"""
from nex.txio import get_asset_attachments
from nex.nex_token import *
from nex.crowdsale import *
from nex.nep5 import *
from nex.owner import *
from boa.interop.Neo.Runtime import GetTrigger, CheckWitness, Notify
from boa.interop.System.ExecutionEngine import GetExecutingScriptHash
from boa.interop.Neo.TriggerType import Application, Verification
from boa.interop.Neo.Storage import *
from boa.interop.Neo.Contract import Migrate
from boa.interop.Neo.Action import RegisterAction

ctx = GetContext()
NEP5_METHODS = ['name', 'symbol', 'decimals', 'totalSupply', 'balanceOf', 'transfer', 'transferFrom', 'approve', 'allowance']

OnTransfer = RegisterAction('transfer', 'addr_from', 'addr_to', 'amount')

def Main(operation, args):
    """

    :param operation: str The name of the operation to perform
    :param args: list A list of arguments along with the operation
    :return:
        bytearray: The result of the operation
    """

    trigger = GetTrigger()

    # This is used in the Verification portion of the contract
    # To determine whether a transfer of system assets ( NEO/Gas) involving
    # This contract's address can proceed
    if trigger == Verification():

        # check if at least 3 of 5 owner signatures are present
        is_owner = check_owners(ctx, 3)

        # If owner, proceed
        if is_owner:
            return True

        # Otherwise, we need to lookup the assets and determine
        # If attachments of assets is ok
        attachments = get_asset_attachments()

        if attachments['sent_from_contract_addr']:
            return False

        return can_exchange(ctx, attachments, True)

    elif trigger == Application():

        for op in NEP5_METHODS:
            if operation == op:
                callingScriptHash = GetCallingScriptHash()
                return handle_nep51(ctx, operation, args, callingScriptHash)

        if operation == 'circulation':
            return get_circulation(ctx)

        elif operation == 'testWhitelist':
            round = args[0]
            addr = args[1]
            return kyc_status(ctx, round, addr)

        elif operation == 'putWhitelist':
            return register_kyc_addr(ctx, args)

        elif operation == 'mintTokens':
            return perform_exchange(ctx)

        elif operation == 'crowdsaleAvailable':
            return crowdsale_available_amount(ctx)

        # the following are administrative methods

        elif operation == 'deploy':
            return deploy()

        elif operation == 'initializeOwners':
            return initialize_owners(ctx)

        elif operation == 'getOwners':
            return get_owners(ctx)

        elif operation == 'checkOwners':
            return check_owners(ctx, 3)

        elif operation == 'switchOwner':
            return switch_owner(ctx, args)

        elif operation == 'ownerMint':
            return owner_mint(ctx, args)

        elif operation == 'migrateContract':
            return migrate(args)

        elif operation == 'mintRemainder':
            return mint_remainder()

        else:
            print("unknown")

        return 'unknown operation'

    return False


def deploy():
    """
    Initial deploy, which places initial amount into circulation
    Requires full owner permission ( 3 of 5 )

    :return:
        bool: Whether the operation was successful
    """

    if not check_owners(ctx, 3):
        return False

    if not Get(ctx, 'initialized'):
        # do deploy logic
        Put(ctx, 'initialized', 1)

        # who or what address do we put the initial amount to?
        # we will put it to the address of the contract

        contract_address = GetExecutingScriptHash()

        contract_balance_key = get_balance_key(contract_address)

        Put(ctx, contract_balance_key, TOKEN_INITIAL_AMOUNT)

        added_to_circ = add_to_circulation(ctx, TOKEN_INITIAL_AMOUNT)

        # dispatch mint
        OnTransfer(False, contract_address, TOKEN_INITIAL_AMOUNT)

        return added_to_circ

    return False


def migrate(args):
    """
    Migrate this contract to a new version

    :param args: list of arguments containing migrating contract info
    :return: Contract
    """
    if not check_owners(ctx, 3):
        return False

    # once migrated, funds held at the contract address are no
    # longer retrievable.  make sure to transfer all funds
    # before doing anything.
    contract_balance_key = get_balance_key(GetExecutingScriptHash())
    current_contract_balance = Get(ctx, contract_balance_key)
    if current_contract_balance > 0:
        print("Cannot migrate yet.  Please transfer all neo/gas and tokens from contract address")
        return False

    if len(args) != 9:
        print("Provide 9 arguments")
        return False

    script = args[0]

    param_list = args[1]
    return_type = args[2]
    properties = args[3]
    name = args[4]
    version = args[5]
    author = args[6]
    email = args[7]
    description = args[8]

    new_contract = Migrate(script, param_list, return_type, properties, name, version, author, email, description)

    return new_contract


def mint_remainder():
    """
    After the crowdsale has ended, there is anticipated to be a small amount
    of NEX remaining unminted from the 50,000,000 total.

    This operation mints this remaining amount to the contract's address

    :return: bool
    """
    if not check_owners(ctx, 3):
        return False

    # check that all owners have minted
    if not have_all_owners_minted(ctx):
        print("All Owners must mint before minting remainder")
        return False

    current_time = GetTime()

    if current_time < ROUND2_END:
        return False

    remainder_amount = TOKEN_TOTAL_SUPPLY - get_circulation(ctx)

    if remainder_amount <= 0:
        print("No remaining tokens")
        return False

    contract_address = GetExecutingScriptHash()

    contract_balance_key = get_balance_key(contract_address)

    current_contract_balance = Get(ctx, contract_balance_key)

    new_contract_balance = current_contract_balance + remainder_amount

    Put(ctx, contract_balance_key, new_contract_balance)

    added_to_circ = add_to_circulation(ctx, remainder_amount)

    # dispatch mint
    OnTransfer(False, contract_address, remainder_amount)

    return added_to_circ
