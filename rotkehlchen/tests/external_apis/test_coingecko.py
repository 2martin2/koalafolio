import pytest

from rotkehlchen.assets.asset import Asset
from rotkehlchen.constants.assets import A_BTC
from rotkehlchen.externalapis.coingecko import Coingecko, CoingeckoAssetData, CoingeckoImageURLs


@pytest.fixture(scope='session')
def session_coingecko():
    return Coingecko()


def assert_coin_data_same(given, expected, compare_description=False):
    if compare_description:
        assert given == expected

    # else
    assert given.identifier == expected.identifier
    assert given.symbol == expected.symbol
    assert given.name == expected.name
    assert given.images.thumb == expected.images.thumb
    assert given.images.small == expected.images.small
    assert given.images.large == expected.images.large


def test_asset_data(session_coingecko):
    expected_data = CoingeckoAssetData(
        identifier='bitcoin',
        symbol='btc',
        name='Bitcoin',
        description='',
        images=CoingeckoImageURLs(
            thumb='https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png?1547033579',
            small='https://assets.coingecko.com/coins/images/1/small/bitcoin.png?1547033579',
            large='https://assets.coingecko.com/coins/images/1/large/bitcoin.png?1547033579',
        ),
    )
    data = session_coingecko.asset_data(A_BTC)
    assert_coin_data_same(data, expected_data)

    expected_data = CoingeckoAssetData(
        identifier='yearn-finance',
        symbol='yfi',
        name='yearn.finance',
        description='Management token for the yearn.finance ecosystem',
        images=CoingeckoImageURLs(
            thumb='https://assets.coingecko.com/coins/images/11849/thumb/yfi-192x192.png?1598325330',  # noqa: E501
            small='https://assets.coingecko.com/coins/images/11849/small/yfi-192x192.png?1598325330',  # noqa: E501
            large='https://assets.coingecko.com/coins/images/11849/large/yfi-192x192.png?1598325330',  # noqa: E501
        ),
    )
    data = session_coingecko.asset_data(Asset('YFI'))
    assert_coin_data_same(data, expected_data, compare_description=True)
