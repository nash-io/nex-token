from nex.nex_token import *

def initialize_owners(ctx):
    """
    Initializes the owners from the hard coded version in the contract
    to a storage based version, so that owners can be swapped in case
    an address in compromised or otherwise changed.

    Also puts the initial 'amount minted' into storage for each address.

    :param ctx: StorageContext
    :return:
    """
    if not Get(ctx, 'owners_initialized'):

        Put(ctx, 'owner1', TOKEN_OWNER1)
        Put(ctx, 'owner2', TOKEN_OWNER2)
        Put(ctx, 'owner3', TOKEN_OWNER3)
        Put(ctx, 'owner4', TOKEN_OWNER4)
        Put(ctx, 'owner5', TOKEN_OWNER5)
        Put(ctx, 'owner1Minted', False)
        Put(ctx, 'owner2Minted', False)
        Put(ctx, 'owner3Minted', False)
        Put(ctx, 'owner4Minted', False)
        Put(ctx, 'owner5Minted', False)

        Put(ctx, 'owners_initialized', True)
        return True

    return False

def have_all_owners_minted(ctx):

    keys = ['owner1Minted', 'owner2Minted', 'owner3Minted', 'owner4Minted', 'owner5Minted']

    for key in keys:
        if not Get(ctx, key):
            return False
    return True

def is_owner_str(owner):
    """
    Determines whether a string is a valid owner string

    :param owner: string identifying an owner
    :return: bool
    """
    if owner == 'owner1' or owner == 'owner2' or owner == 'owner3' or owner == 'owner4' or owner == 'owner5':
        return True
    return False


def get_owners(ctx):
    """
    Retrieves the current list of owners from storage

    :param ctx: StorageContext
    :return: list: a list of owners
    """
    return [Get(ctx, 'owner1'), Get(ctx, 'owner2'), Get(ctx, 'owner3'), Get(ctx, 'owner4'), Get(ctx, 'owner5')]

def check_owners(ctx, required):
    """

    Determines whether or not this transaction was signed with at least 3 of 5 owner signatures

    :param ctx: StorageContext
    :return: bool
    """
    if not Get(ctx, 'owners_initialized'):
        print("Please run initializeOwners")
        return False

    total = 0

    owners = get_owners(ctx)

    for owner in owners:
        if CheckWitness(owner):
            total += 1
    return total >= required


def switch_owner(ctx, args):
    """
    Switch the script hash of an owner to a new one.
    Requires full owner permission ( 3 of 5 )

    :param args: a list of arguments with the owner name first ( eg 'owner1') and a script hash second
    :return: bool
    """
    if not check_owners(ctx, 3):
        return False

    if len(args) != 2:
        return False

    which_owner = args[0]

    if not is_owner_str(which_owner):
        return False

    new_value = args[1]

    if len(new_value) == 20:
        Put(ctx, which_owner, new_value)
        return True

    return False
