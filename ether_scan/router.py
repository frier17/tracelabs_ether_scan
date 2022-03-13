import itertools
from typing import Mapping, Any, Sequence, Union, Dict
import requests
import re as regex
from requests.exceptions import HTTPError
from fastapi import FastAPI, Request, Response, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from ether_scan import settings
from ether_scan import util
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# Define lookup functions to pull information or datasets
def fetch_address_data(address: str) -> Any:
    pattern = r'^0x[a-fA-F0-9]{40}$'
    checker = regex.compile(pattern)
    if not checker.match(address):
        raise ValueError('Invalid block hash or number provided')
    try:
        data = requests.get(f'{settings.BLOCKCYPHER_ADDRESS_DETAIL_URL}/{address}/full').json()
        return data
    except HTTPError as err:
        logger.critical(err.__traceback__)
    except Exception as ex:
        logger.log(logging.INFO, ex.__traceback__)


def fetch_address_txlist(address: str, params: Mapping = None) -> Any:
    """
    Retrieve full blockchain or transaction list data for the given address using the etherscan.io API endpoint
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
        params = {x: y for x, y in params.items() if x in allowed_keys}
        params.update(
            {'module': 'account', 'action': 'txlist', 'address': address, 'apikey': settings.ETHERSCAN_API_KEY})
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
    Retrieve the detail of a transaction from the Ethereum blockchain using the transaction hash.
    !!Make call to BlockCypher API endpoint as etherscan.io API does not provide a transaction detail endpoint at
    time of writing
    :param tranx: transaction hash
    :type tranx: string
    :return: details of a transaction as a dictionary or mapped data structure
    :rtype: mapping
    """
    pattern = r'^(0x)?[a-fA-F0-9]{64,66}$'
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


def fetch_block_data(block: Union[int, str] = None) -> Any:
    """
    Retrieve the detail of a block on Ethereum blockchain using the block hash or block height/number.
    !! Make call to BlockCypher API block URL as etherscan.io does not provide a transaction detail endpoint at
    time of writing
    :param block: block hash or number
    :type block: int or string
    :return: block detail as a dictionary or mapped data structure
    :rtype: mapping
    """
    block = str(block)

    hash_pattern = r'^(0x)?[a-fA-F0-9]{64,66}$'
    hash_checker = regex.compile(hash_pattern)

    height_pattern = r'[0-9]{1,66}'
    height_checker = regex.compile(height_pattern)

    if hash_checker.match(block):
        if block.startswith('0x'):
            block = block[2:]
        url = f'{settings.BLOCKCYPHER_BLOCK_BY_HASH_URL}/{block}'
        try:
            return requests.get(url).json()
        except HTTPError as err:
            logger.critical(err.__traceback__)
        except Exception as ex:
            logger.log(logging.INFO, ex.__traceback__)
    elif height_checker.match(block):
        url = f'{settings.BLOCKCYPHER_BLOCK_BY_HEIGHT_URL}/{block}'
        try:
            return requests.get(url).json()
        except HTTPError as err:
            logger.critical(err.__traceback__)
        except Exception as ex:
            logger.log(logging.INFO, ex.__traceback__)
    else:
        raise ValueError('Invalid block hash or number provided')


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


def generate_tnx_monetary_data(tranx: Any, currency: str = 'USD') -> Any:
    # Parse iterator or list of tranx to have monetary value field
    def _parse_to_amount(tnx: Any) -> Any:
        total = tnx.get('total', None) or tnx.get('value', None)
        if total:
            total = total / 10e18
        monetary_value = fetch_current_price('ETH', total, currency)
        tnx['current_value'] = monetary_value
        return tnx

    if isinstance(tranx, Sequence) and not isinstance(tranx, str):
        return map(lambda a: _parse_to_amount(a), tranx)
    else:
        raise ValueError('Invalid iterator or list parsed as transaction list')


def generate_addr_monetary_data(address: Any, token: str = 'ETH', currency: str = 'USD') -> Any:
    # Parse address data to have monetary value
    total_sent = util.extract_data('total_sent', address)
    if total_sent:
        total_sent = total_sent / 10e18
    else:
        total_sent = 0.0

    balance = util.extract_data('balance', address)
    if balance:
        balance = balance / 10e18
    else:
        balance = 0.0
    final_balance = util.extract_data('final_balance', address)
    if final_balance:
        final_balance = final_balance / 10e18
    else:
        final_balance = 0.0

    total_money = fetch_current_price(token, total_sent, currency)
    balance_money = fetch_current_price(token, balance, currency)
    final_balance_money = fetch_current_price(token, final_balance, currency)
    address.update({
        'total_money_sent': total_money,
        'money_balance': balance_money,
        'final_money_balance': final_balance_money,
        'fiat_currency': currency
    })
    return address


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


@app.get("/", description="Home page of the Ether Scan application demo", response_class=HTMLResponse)
async def home(request: Request) -> Response:
    # load HTML file from templates directory
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/docs#", description="Application default documentation page based on Swagger")
async def doc() -> None:
    ...


# define async function to pull ethereum data using ether.io API
@app.post("/scan", description="Specify an API endpoint which scans the Ethereum blockchain for all normal "
                               "transactions sent of a specified wallet or address")
async def scan_wallet(payload: Dict = Body(..., description="Posted data with address and block values")) -> Mapping:
    # validate wallet is in right format
    wallet = payload.get('address')
    block = payload.get('block')
    if not isinstance(wallet, str):
        raise Exception('Wallet or address must be a valid string')
    else:
        pattern = r'^0x[a-fA-F0-9]{40}$'
        checker = regex.compile(pattern)
        wallet = str(wallet).strip()
        if not checker.match(wallet):
            raise Exception('Invalid wallet address pattern supplied. Ensure address is a valid Ethereum address '
                            'without spaces or special characters')

    address_data = fetch_address_data(wallet)
    address_summary = util.address_summary(address_data)
    address_summary_monetary = generate_addr_monetary_data(address_summary)
    trx_lists = util.parse_transactions(util.extract_data('txs', address_data))

    if block:
        trx_lists = itertools.takewhile(lambda x: x.get('block_height') >= int(block) or x.get('block_hash') == block,
                                        trx_lists)
        transactions = [a for a in trx_lists]
        return {
            'address_monetary_summary': address_summary_monetary,
            'transaction_lists': transactions,
            'block_detail': fetch_block_data(block)
        }
    else:
        transactions = [a for a in trx_lists]
        return {
            'address_monetary_summary': address_summary_monetary,
            'transaction_lists': transactions
        }


@app.post("/scan/block", description="An alternate scan function using EtherScan API. "
                                     "Scans the Ethereum blockchain for transactions associated with an address. "
                                     "Information returned concerns financial and block data for each transaction "
                                     "retrieved")
def scan_wallet_by_block(wallet: str, start_block: str = None, end_block: str = None, page: int = 1, offset: int = 10,
                         sort: str = 'asc'):
    if not isinstance(wallet, str):
        raise Exception('Wallet or address must be a valid string')
    else:
        pattern = r'^0x[a-fA-F0-9]{40}$'
        checker = regex.compile(pattern)
        wallet = str(wallet).strip()
        if not checker.match(wallet):
            raise Exception('Invalid wallet address pattern supplied. Ensure address is a valid Ethereum address '
                            'without spaces or special characters')

    address_data = fetch_address_data(wallet)
    address_summary = util.address_summary(address_data)
    out = fetch_address_txlist(address=wallet, params={
        'startblock': start_block, 'endblock': end_block, 'page': page, 'offset': offset, 'sort': sort
    })
    data = util.extract_data('result', out)
    trx_list = generate_tnx_monetary_data(data)

    blocks = (util.extract_data('blockHash', x) for x in data)
    block_data = (fetch_block_data(block=x) for x in blocks)
    trx_list = (x.update({'block_detail': y}) for x in trx_list for y in block_data if
                x.get('blockNumber') == y.get('height') or x.get('blockHash')[2:] == y.get('hash'))

    return {'tranx_statistics': trx_list, 'address_summary': address_summary}
