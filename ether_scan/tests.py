from unittest import TestCase
from ether_scan import router


class TestEtherScan(TestCase):

    def setUp(self) -> None:
        self.test_wallet = '0xe87dfcee6cab984fe689b035794f945ff1d57a5e'
        self.sample_block = '7720873'
        self.sample_tranx = '0xa72aac8075c6bb24a9e02883e9c81d7c2f1951434030394956fa8d44cd845207'

    def tearDown(self) -> None:
        del self.test_wallet
        del self.sample_block
        del self.sample_tranx

    def test_fetch_data(self) -> None:
        # pull request from router function to fetch server data using test_wallet and sample_block parameters
        data = router.fetch_address_txlist(address=self.test_wallet)
        assert data

    def test_fetch_transaction_data(self) -> None:
        data = router.fetch_transaction_data(self.sample_tranx)
        assert data
        assert data.get('hash') in self.sample_tranx
        assert data.get('confirmations') > 0

    def test_fetch_block_data(self) -> None:
        data = router.fetch_block_data(height=self.sample_block)
        print(data.get('height'))
        print(self.sample_block)
        assert data
        assert data.get('hash')
        assert data.get('height')
