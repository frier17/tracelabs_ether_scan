from typing import Mapping, Any
import requests
import re as regex
from requests.exceptions import HTTPError
from fastapi import FastAPI
from ether_scan import settings
from ether_scan import util
import logging

logger = logging.getLogger(__name__)

app = FastAPI()


# Define lookup functions to pull information or datasets
def fetch_address_data(address: str, params: Mapping = None) -> Any:
    """
    Retrieve full blockchain data for the given address using the etherscan.io API endpoint
    :param address: Ethereum address used to query the network
    :type address: textual data or string
    :param params: dictionary of query parameter that can be used to filter server response.
    Dictionary keys should represent the API query terms while value should be assigned value for the query term.
    Accepted values based on etherscan.io specifications are:
        start_block: str = None,
        end_block: str = None,
        page: int = 1,
        offset: int = 10,
        sort: str = 'asc'
    :return: dictionary or any suitable object with the address information meeting specified param
    :rtype: Any
    """
    pattern = r'^0x[a-fA-F0-9]{40}$'
    checker = regex.compile(pattern)
    if not checker.match(address):
        raise ValueError('Invalid block hash or number provided')
    if params:
        # prepare query string for request
        allowed_keys = ['module', 'action', 'startblock', 'endblock', 'page', 'offset', 'sort']
        params = {x: y for x, y in params if x in allowed_keys}
        params.update({'address': address, 'apikey': settings.ETHERSCAN_API_KEY})
    else:
        defaults = {'startblocdk': 0, 'endblock': 99999999, 'page': 1, 'offset': 10, 'sort': 'asc'}
        params = {'module': 'account', 'action': 'txlist', 'address': address, 'apikey': settings.ETHERSCAN_API_KEY}
        params.update(defaults)

    try:
        data = requests.get(settings.WALLET_TRANSACTION_URL, params=params).json()
        return data
    except HTTPError as err:
        logger.critical(err.__traceback__)
    except Exception as ex:
        logger.log(logging.INFO, ex.__traceback__)


def fetch_transaction_data(tranx: str) -> Any:
    """
    !! Make call to BlockCypher API endpoint as etherscan.io API does not provide a transaction detail endpoint at
    time of writing
    :param tranx:
    :type tranx:
    :return:
    :rtype:
    """
    pattern = r'^0x[a-fA-F0-9]{64,66}$'
    checker = regex.compile(pattern)
    if not checker.match(tranx):
        raise ValueError('Invalid transaction hash provided')
    url = f'{settings.BLOCKCYPHER_TRANSACTION_DETAILS_URL}/{tranx}'
    try:
        return requests.get(url).json()
    except HTTPError as err:
        logger.critical(err.__traceback__)
    except Exception as ex:
        logger.log(logging.INFO, ex.__traceback__)


def fetch_block_data(block: str = None, height: str = None) -> Any:
    """
    !! Make call to BlockCypher API block URL as etherscan.io does not provide a transaction detail endpoint at
    time of writing
    :param block:
    :type block:
    :return:
    :rtype:
    """
    if block and not height:
        pattern = r'^0x[a-fA-F0-9]{8,66}$'
        checker = regex.compile(pattern)
        if not checker.match(block):
            raise ValueError('Invalid block hash or number provided')
        url = f'{settings.BLOCKCYPHER_BLOCK_BY_HASH_URL}/{block}'
        try:
            return requests.get(url).json()
        except HTTPError as err:
            logger.critical(err.__traceback__)
        except Exception as ex:
            logger.log(logging.INFO, ex.__traceback__)
    elif height and not block:
        pattern = r'^[0-9]{1,66}$'
        checker = regex.compile(pattern)
        if not checker.match(height):
            raise ValueError('Invalid block hash or number provided')
        url = f'{settings.BLOCKCYPHER_BLOCK_BY_HEIGHT_URL}/{height}'
        try:
            return requests.get(url).json()
        except HTTPError as err:
            logger.critical(err.__traceback__)
        except Exception as ex:
            logger.log(logging.INFO, ex.__traceback__)


def fetch_current_price(token: str, quantity: float, currency: str = 'USD') -> str:
    """
    Retrieve the current USD or specified currency value of Ethereum using the CryptoCompare API endpoint
    :param token: quantity of ether to convert
    :type token: string
    :param quantity: quantity of ether to convert
    :type quantity: float or integer
    :param currency: specified target currency which the ether is converted to.
    Currency format should be ISO 4217 standard
    :type currency: string
    :return: The value of ether in the target currency as a numerical string
    :rtype: string
    """

    def _currency_exchange(source: Any, target: Any, url: str = None) -> Any:
        # convert source currency to target
        if source == target or str(source).upper() == str(target).upper():
            return 1.0

        if isinstance(source, str):
            assets = settings.APPROVED_TOKENS
            if source not in assets:
                raise ValueError('Invalid token type specified. A restricted list of tokens is used for demonstration '
                                 'purposes')

        if isinstance(target, (list, tuple)):
            approved = settings.APPROVED_FIATS
            if all([str(x).upper() for x in target if str(x).upper() in approved]):
                target = ','.join(target)
        elif isinstance(target, str):
            # check if target is not in list of approved currencies
            if len(target) > 3:
                raise RuntimeError('Invalid currency specified. A restricted list of currencies is used for '
                                   'demonstration purposes')
        if not url:
            url = f'{settings.CRYPTO_COMPARE_SINGLE_SYMBOL_PRICE}?fsym={source}&tsyms={target}'
        out = requests.get(url, headers={'authorization': f'Apikey {settings.CRYPTO_COMPARE_API}'})
        if out.status_code >= 200 or out.status_code < 400:
            data = out.json()
            if isinstance(target, str):
                rate = util.extract_data(target.upper(), data)
                return float(rate)
            else:
                return data
        return 0

    exchange_rate = _currency_exchange(token, target=currency)
    if exchange_rate:
        value = exchange_rate * quantity
        return str(value)


def fetch_historic_price(token: str, timestamp: str, quantity: float = 0.0, currency: str = 'USD',
                         flag: str = 'MidHighLow') -> Mapping:
    """
    Retrieve the Closed; average of the Mid, High, Low; total Volume from, and Volume to information of a currency
    trading pair using the CryptoCompare API endpoint
    :param token: Retrieve the current USD or specified currency value of Ethereum using the CryptoCompare API endpoint
    :type token: string
    :param timestamp: specified time using UNIX timestamp format
    :type timestamp: integer
    :param quantity: the quantity of token to convert
    :type quantity: float
    :param currency: target currency or list of currencies to apply the conversion.
    For demonstration purposes, only single currency is used. The currency is specified in ISO 4217 format
    :type currency: string
    :param flag: indicator of the calculation type to use for querying historical token value for the specified currency
    :type flag: string
    :return: Dictionary of the token with corresponding historical conversion rate for specified time and calculation
    type as specified in CryptoCompare
    (see: https://min-api.cryptocompare.com/documentation?key=Historical&cat=dataPriceHistorical)
    :rtype: dict
    """
    url = f'{settings.CRYPTO_COMPARE_OHLCV_BY_TS}?fsym={token}&tsyms={currency}&ts={timestamp}&calculationType={flag}'
    data = requests.get(url, headers={'authorization': f'Apikey {settings.CRYPTO_COMPARE_API}'}).json()
    if flag in ('MidHighLow', 'Close'):
        rate = util.extract_data(currency, data)
        return {f'{token}': quantity * rate}
    else:
        return data


# define async function to pull ethereum data using ether.io API
@app.post("/", description="Specify an API endpoint which scans the Ethereum blockchain for all normal "
                           "transactions sent of a specified wallet or address")
async def scan_wallet(wallet: str, start_block: str = None, end_block: str = None, page: int = 1, offset: int = 10,
                      sort: str = 'asc') -> Mapping:
    # validate wallet is in right format
    if not isinstance(wallet, str):
        raise Exception('Wallet or address must be a valid string')
    else:
        pattern = r'^0x[a-fA-F0-9]{40}$'
        checker = regex.compile(pattern)
        wallet = str(wallet).strip()
        if not checker.match(wallet):
            raise Exception('Invalid wallet address pattern supplied. Ensure address is a valid Ethereum address '
                            'without spaces or special characters')

    data = fetch_address_data(address=wallet, params={
        'startblock': start_block, 'endblock': end_block, 'page': page, 'offset': offset, 'sort': sort
    })
    blocks = [util.extract_data('blockNumber', x) for x in data]
    block_data_by_number = [fetch_block_data(x) for x in blocks]
    trans = [util.extract_data('hash', x) for x in data]
    tranx_data = [fetch_transaction_data(x) for x in trans]
    # get all transactions associated to address
    # get all block information associated with transaction
    # generate the various statistics and information objects
    tranx_statistics = [util.generate_tranx_statistics(x) for x in tranx_data]
    block_statistics = [util.generate_block_statistics(x) for x in block_data_by_number]
    monetary_object = util.generate_monetary_object(data)
    historic_object = util.generate_historic_object(data)
    block_information = util.generate_block_information(data)
    tranx_information = util.generate_transaction_information(data)
    return {
        'tranx_statistics': tranx_statistics,
        'block_statistics': block_statistics,
        'monetary_object': monetary_object,
        'historic_object': historic_object,
        'block_information': block_information,
        'tranx_information': tranx_information,
    }

