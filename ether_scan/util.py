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


def parse_transactions(trans: List) -> Any:
    ...


def generate_block_statistics(block: Mapping) -> Any:
    return {
        'size': extract_data('size', block),
        'time': extract_data('time', block),
        'received_time': extract_data('received_time', block),
    }


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


def generate_monetary_object(data: Any) -> Any:
    ...


def generate_historic_object(data: Any) -> Any: ...


def generate_block_information(data: Any) -> Any: ...


def generate_transaction_information(data: Any) -> Any: ...
