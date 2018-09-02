from boa.interop.Neo.Blockchain import GetHeight
from boa.interop.Neo.Runtime import CheckWitness, GetTime, Notify
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put
from boa.builtins import concat, verify_signature
from nex.nex_token import *
from nex.owner import *
from nex.txio import get_asset_attachments, neo_asset_id, gas_asset_id
from boa.interop.Neo.Runtime import Serialize, Deserialize
from boa.interop.System.ExecutionEngine import GetScriptContainer

OnTransfer = RegisterAction('transfer', 'addr_from', 'addr_to', 'amount')
OnRefund = RegisterAction('refund', 'addr_to', 'amount', 'asset')
OnMint = RegisterAction('mint', 'addr_to', 'amount')
OnKYCRegister = RegisterAction('kyc_registration', 'address')

KYC_REGISTRAR = b'y\xa3\xf4\xab\xfbg,\xd9\xec\xb5k\x81HX\xe8I\xf5K\xdd\xa1'

KYC_PREFIX = b'kycApprove'

LAST_TX_KEY = b'lastTX'

def get_kyc_prefixed_addr(round, addr):
    return concat(KYC_PREFIX, concat(round, addr))

def kyc_status(ctx, rnd, addr):
    """
    Gets the KYC Status of an address

    :param args:list a list of arguments
    :return:
        bool: Returns the kyc status of an address
    """
    kycKey = get_kyc_prefixed_addr(rnd, addr)
    if len(kycKey) == 36:
        return Get(ctx, kycKey)
    return False

def register_kyc_addr(ctx, args):

    # KYC registrar wallet requried
    if not CheckWitness(KYC_REGISTRAR):
        print("Must have KYC Registrar permission")
        return False

    if len(args) != 2:
        print("incorrect arg len")
        return False

    rnd = args[0]
    addrs = args[1]
    for addr in addrs:
        kycKey = get_kyc_prefixed_addr(rnd, addr)
        if len(kycKey) == 36:
            Put(ctx, kycKey, True)
            OnKYCRegister(addr)
        else:
            return False
    return True


def perform_exchange(ctx):
    """

     :param token:Token The token object with NEP5/sale settings
     :return:
         bool: Whether the exchange was successful
     """
    last_tx = Get(ctx, LAST_TX_KEY)
    current_tx = GetScriptContainer().Hash
    if last_tx == current_tx:
        return False
    Put(ctx, LAST_TX_KEY, current_tx)

    attachments = get_asset_attachments()  # [receiver, sender, neo, gas]

    # this looks up whether the exchange can proceed
    exchange_ok = can_exchange(ctx, attachments, False)

    sender = attachments['sender']

    if not exchange_ok:
        # This should only happen in the case that there are a lot of TX on the final
        # block before the total amount is reached.  An amount of TX will get through
        # the verification phase because the total amount cannot be updated during that phase
        # because of this, there should be a process in place to manually refund tokens
        if attachments['sent_neo'] > 0:
            OnRefund(sender, attachments['sent_neo'], neo_asset_id)

        if attachments['sent_gas'] > 0:
            OnRefund(sender, attachments['sent_gas'], gas_asset_id)

        return False

    balance_key = get_balance_key(sender)

    # lookup the current balance of the address
    current_balance = Get(ctx, balance_key)

    new_nex_tokens = calculate_exchange_amount(attachments)

    # add it to the the exchanged tokens and persist in storage
    new_total = new_nex_tokens + current_balance
    Put(ctx, balance_key, new_total)

    # update the in circulation amount
    result = add_to_circulation(ctx, new_nex_tokens)

    # dispatch transfer event
    OnTransfer(False, sender, new_nex_tokens)

    return True

def calculate_exchange_amount(attachments):

    amount_requested_neo = attachments['sent_neo'] * TOKENS_PER_NEO / 100000000
    amount_requested_gas = attachments['sent_gas'] * TOKENS_PER_GAS / 100000000

    amount_requested = amount_requested_neo + amount_requested_gas

    return amount_requested

def can_exchange(ctx, attachments, verify_only):
    """
    Determines if the contract invocation meets all requirements for the ICO exchange
    of neo or gas into NEP5 Tokens.
    Note: This method can be called via both the Verification portion of an SC or the Application portion

    When called in the Verification portion of an SC, it can be used to reject TX that do not qualify
    for exchange, thereby reducing the need for manual NEO or GAS refunds considerably

    :param attachments:Attachments An attachments object with information about attached NEO/Gas assets
    :return:
        bool: Whether an invocation meets requirements for exchange
    """

    if attachments['sent_neo'] == 0 and attachments['sent_gas'] == 0:
        print("No neo or gas attached")
        return False

    amount_requested = calculate_exchange_amount(attachments)

    exchange_ok = calculate_can_exchange(ctx, amount_requested, attachments['sender'], verify_only)

    return exchange_ok


def calculate_can_exchange(ctx, amount, address, verify_only):
    """
    Perform custom token exchange calculations here.

    :param amount:int Number of tokens to convert from asset to tokens
    :param address:bytearray The address to mint the tokens to
    :return:
        bool: Whether or not an address can exchange a specified amount
    """
    timestap = GetTime()

    current_in_circulation = Get(ctx, TOKEN_CIRC_KEY)
    new_amount = current_in_circulation + amount

    if new_amount > TOKEN_TOTAL_SUPPLY:
        return False

    if timestap >= ROUND1_START and timestap <= ROUND1_END:

        print("Minting Round 1")

        r1key = concat(address, MINTED_ROUND1_KEY)

        # the following looks up whether an address has been
        # registered with the contract for KYC regulations
        # check if they have already exchanged in round 1
        # if not, then save the exchange for limited round
        if amount <= MAX_EXCHANGE_ROUND1 and kyc_status(ctx, 'round1', address) and not Get(ctx, r1key):

            if not verify_only:
                Put(ctx, r1key, True)
            return True

    if timestap >= ROUND2_START and timestap <= ROUND2_END:

        print("Minting round 2")

        r2key = concat(address, MINTED_ROUND2_KEY)

        if amount <= MAX_EXCHANGE_ROUND2 and kyc_status(ctx, 'round2', address) and not Get(ctx, r2key):

            if not verify_only:
                Put(ctx, r2key, True)

            return True

    print("Not eligible")
    return False


def owner_mint(ctx, args):
    """
    This method allows owners to mint their share at 500k increments over 2 years
    It does not require 'full' owner approval ( 3 of 5 sigs) but only approval
    by the owner wishing to mint.

    :param args: list
    :return: bool
    """
    if len(args) != 1:
        return False

    which_owner = args[0]

    if not is_owner_str(which_owner):
        return False

    current_owner_addr = Get(ctx, which_owner)

    if not CheckWitness(current_owner_addr):
        return False

    amount_to_mint = PER_OWNER_TOTAL

    # get the key used to track mint amount per owner
    owner_minted_key = concat(which_owner, 'Minted')

    # lookup whether owner has minted
    already_minted = Get(ctx, owner_minted_key)

    if already_minted:
        print("Owner already minted")
        return False

    # update that owner has minted
    Put(ctx, owner_minted_key, True)

    # Add this amount to circulation
    added_to_circ = add_to_circulation(ctx, amount_to_mint)

    # dispatch mint
    OnTransfer(False, current_owner_addr, amount_to_mint)

    # now get current owners balance

    owner_balance_key = get_balance_key(current_owner_addr)

    current_balance = Get(ctx, owner_balance_key)
    # update it with the amount to mint
    new_balance = current_balance + amount_to_mint
    # now persist the new balance
    Put(ctx, owner_balance_key, new_balance)

    return True
