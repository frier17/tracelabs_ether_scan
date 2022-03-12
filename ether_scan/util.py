import re as regex
import datetime
from dateutil import tz
from typing import Mapping, Any, List


# Define utility functions

def extract_data(field: str, data: Mapping, sentinel: Any = None) -> Any:
    # Extract given field from possibly nested data structure
    if isinstance(data, Mapping):
        if field in data:
            return data.get(field, None)
        for k, v in data.items():
            if isinstance(v, Mapping):
                value = extract_data(field, v)
                if value is not sentinel:
                    return value


def convert_to_utc(time: str) -> datetime.datetime:
    # convert time format to datetime object that is aware of timezone
    # sample time format 2015-08-07T11:45:53Z as UTC datetime
    date_pattern = r'\d{4}\-\d{2}\-\d{2}'
    timestamp_pattern = r'\d{4,}'
    date_checker = regex.compile(date_pattern)
    timestamp_checker = regex.compile(timestamp_pattern)
    if date_checker.match(time):
        try:
            dt = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
            dt.astimezone(tz.UTC)
            return dt
        except ValueError:
            dt = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')
            dt.astimezone(tz.UTC)
            return dt
    elif timestamp_checker.match(time):
        # Assume etherscan.io timestamp is in UTC
        dt = datetime.datetime.fromtimestamp(float(time), tz.UTC)
        return dt


def parse_transactions(trans: List) -> Any:
    """
    Parse a list of transactions into details of the format specified or consumable by the user interface.
    This function converts based transaction mapping into a more human-readable object. Specified fields of the target
    format will include:
    Transaction Hash as txn_hash (the given transaction hash as saved on the blockchain)
    Block Hash as block (the hash of the block in which the transaction was added or confirmed)
    Block Height as block_height (the block height or number)
    Transaction Fees as fees (the fees paid for this transaction. Fees are saved in WEI using for the BlockCypher API)
    Value transferred in ether or token as total (the total number of token transferred)
    Sender's address as input_address (the address from which token was sent)
    Recipient's address as output_address (the address to which token was sent)
    Double spend as double_spend (a boolean flag that confirms if the transaction is a double spend or had been used)
    Confirmed on as confirmed (the time specified in UTC that transaction was confirmed)
    Received by as  received (the time specified in UTC that transaction was received. Same as confirmed)
    Gas used as gas_used (the amount of gas used for this transaction)
    :param trans: list of transactions to parse
    :type trans: list
    :return: list of parsed transaction objects as an iterator
    :rtype: iterator
    """

    def _convert_tranx(tnx) -> Any:
        confirmed = extract_data('confirmed', tnx)
        received = extract_data('received', tnx)
        now = datetime.datetime.utcnow()
        date_format = '%Y-%m-%d %H:%M:%S UTC'
        if confirmed:
            confirmed = convert_to_utc(confirmed)
        if received:
            received = convert_to_utc(received)
        tnx['confirmed'] = confirmed.strftime(date_format)
        tnx['received'] = received.strftime(date_format)
        age = now - received
        tnx['age'] = str(age)
        return tnx

    parsing_trans = map(lambda x: _convert_tranx(x), trans)
    return parsing_trans


def generate_tranx_statistics(tranx: Mapping) -> Any:
    # For a given tranx object or mapping retrieve value and gas
    return {
        'hash': extract_data('hash', tranx),
        'value': extract_data('total', tranx),
        'gas': extract_data('gas_used', tranx),
        'fees': extract_data('fees', tranx)
    }


def address_summary(address: Mapping) -> Any:
    return {
        'address': extract_data('address', address),
        'total_received': extract_data('total_received', address),
        'total_sent': extract_data('total_sent', address),
        'balance': extract_data('balance', address),
        'unconfirmed_balance': extract_data('unconfirmed_balance', address),
        'final_balance': extract_data('final_balance', address),
        'n_tx': extract_data('n_tx', address),
        'unconfirmed_n_tx': extract_data('unconfirmed_n_tx', address),
        'final_n_tx': extract_data('final_n_tx', address),
    }


def generate_historic_object(data: Any) -> Any: ...


def generate_block_information(data: Any) -> Any: ...


def generate_transaction_information(data: Any) -> Any: ...
