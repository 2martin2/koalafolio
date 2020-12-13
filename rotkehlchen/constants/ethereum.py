# flake8: noqa

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import requests

from rotkehlchen.chain.ethereum.contracts import EthereumContract
from rotkehlchen.serialization.deserialize import deserialize_ethereum_address

MAX_BLOCKTIME_CACHE = 250  # 55 mins with 13 secs avg block time
ZERO_ADDRESS = deserialize_ethereum_address('0x0000000000000000000000000000000000000000')
AAVE_ETH_RESERVE_ADDRESS = deserialize_ethereum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE')

def _get_latest_data(data_directory: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Gets the latest assets either locally or from the remote

    Checks the remote (github) and if there is a newer file there it pulls it,
    saves it and its md5 hash locally and returns the new assets.

    If there is no new file (same hash) or if there is any problem contacting the remote
    then the builtin assets file is used.
    """
    our_downloaded_contracts = data_directory / 'assets' / 'eth_contracts.json'
    our_downloaded_abi_entries = data_directory / 'assets' / 'eth_abi.json'
    try:
        # we need to download and save the contracts from github
        response = requests.get(
            'https://raw.githubusercontent.com/rotki/rotki/develop/rotkehlchen/data/eth_contracts.json')  # noqa: E501
        remote_contract_data = response.text
        # we need to download and save the abi from github
        response2 = requests.get(
            'https://raw.githubusercontent.com/rotki/rotki/develop/rotkehlchen/data/eth_abi.json')
        remote_abi_data = response2.text

        # Make sure directory exists
        (data_directory / 'assets').mkdir(parents=True, exist_ok=True)
        # Write the files
        with open(our_downloaded_contracts, 'w') as f:
            f.write(remote_contract_data)
        with open(our_downloaded_abi_entries, 'w') as f:
            f.write(remote_abi_data)

        return json.loads(remote_contract_data), json.loads(remote_abi_data)

        # else, continue without new data
    except (requests.exceptions.ConnectionError, KeyError, json.decoder.JSONDecodeError):
        pass

    if our_downloaded_contracts.is_file() and our_downloaded_abi_entries.is_file():
        with open(our_downloaded_contracts, 'r') as f:
            remote_contract_data = f.read()
        with open(our_downloaded_abi_entries, 'r') as f:
            remote_abi_data = f.read()
        return json.loads(remote_contract_data), json.loads(remote_abi_data)

    # no local data and no remote data available
    return None, None


def _attempt_initialization(
        data_directory: Optional[Path]
) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
    """Reads the ethereum data from the remote

    1. If it's the very first time data is initialized (and data directory is not given)
    then just get assets from the builtin file
    2. If data directory is still not given but we have some saved assets return them directly
    3. If data directory is given then we can finally do the comparison of local
    saved and builtin file with the remote and return the most recent assets.

    Returns a tuple of the most recent data mapping it can get and a boolean denoting
    if the remote check happened or not.
    """
    if data_directory:
        # we got the data directory so we can finally do the remote check
        contracts, abi_entries = _get_latest_data(data_directory)
        return contracts, abi_entries, True
    return None, None, False

class EthereumConstants():
    __instance = None
    contracts: Dict[str, Dict[str, Any]] = {}
    abi_entries: Dict[str, List[Dict[str, Any]]] = {}

    def __new__(
            cls,
            data_directory: Path = None,
    ) -> 'EthereumConstants':
        if EthereumConstants.__instance is not None:
            if EthereumConstants.__instance.remote_check_happened:  # type: ignore
                return EthereumConstants.__instance

            # else we still have not performed the remote check
            contracts, abi_entries, check_happened = _attempt_initialization(
                data_directory=data_directory
            )
        else:
            # first initialization
            contracts, abi_entries, check_happened = _attempt_initialization(
                data_directory=data_directory
            )
            EthereumConstants.__instance = object.__new__(cls)

        EthereumConstants.__instance.contracts = contracts
        EthereumConstants.__instance.abi_entries = abi_entries
        EthereumConstants.__instance.remote_check_happened = check_happened

        return EthereumConstants.__instance

    @staticmethod
    def get() -> Dict[str, Dict[str, Any]]:
        return EthereumConstants().contracts

    @staticmethod
    def contract_or_none(name: str) -> Optional[EthereumContract]:
        """Gets details of an ethereum contract from the contracts json file

        Returns None if missing
        """
        contract = EthereumConstants().contracts.get(name, None)
        if contract is None:
            return None

        return EthereumContract(
            address=contract['address'],
            abi=contract['abi'],
            deployed_block=contract['deployed_block'],
        )

    @staticmethod
    def contract(name: str) -> EthereumContract:
        """Gets details of an ethereum contract from the contracts json file

        Missing contract is an error
        """
        contract = EthereumConstants().contract_or_none(name)
        assert contract, f'No contract data for {name} found'
        return contract

    @staticmethod
    def abi_or_none(name: str) -> Optional[List[Dict[str, Any]]]:
        """Gets abi of an ethereum contract from the abi json file

        Returns None if missing
        """
        return EthereumConstants().abi_entries.get(name, None)

    @staticmethod
    def abi(name: str) -> List[Dict[str, Any]]:
        abi = EthereumConstants().abi_or_none(name)
        assert abi, f'No abi for {name} found'
        return abi

# Latest contract addresses are in the makerdao changelog. These values are taken from here:
# https://changelog.makerdao.com/releases/mainnet/1.1.3/contracts.json


MAKERDAO_DAI_JOIN = lambda: EthereumConstants().contract('MAKERDAO_DAI_JOIN')
MAKERDAO_CDP_MANAGER = lambda: EthereumConstants().contract('MAKERDAO_CDP_MANAGER')
MAKERDAO_GET_CDPS = lambda: EthereumConstants().contract('MAKERDAO_GET_CDPS')
MAKERDAO_PROXY_REGISTRY = lambda: EthereumConstants().contract('MAKERDAO_PROXY_REGISTRY')
MAKERDAO_SPOT = lambda: EthereumConstants().contract('MAKERDAO_SPOT')
MAKERDAO_POT = lambda: EthereumConstants().contract('MAKERDAO_POT')
MAKERDAO_VAT = lambda: EthereumConstants().contract('MAKERDAO_VAT')
MAKERDAO_ETH_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_ETH_A_JOIN')
MAKERDAO_ETH_B_JOIN = lambda: EthereumConstants().contract('MAKERDAO_ETH_B_JOIN')
MAKERDAO_BAT_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_BAT_A_JOIN')
MAKERDAO_USDC_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_USDC_A_JOIN')
MAKERDAO_USDC_B_JOIN = lambda: EthereumConstants().contract('MAKERDAO_USDC_B_JOIN')
MAKERDAO_USDT_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_USDT_A_JOIN')
MAKERDAO_WBTC_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_WBTC_A_JOIN')
MAKERDAO_KNC_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_KNC_A_JOIN')
MAKERDAO_MANA_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_MANA_A_JOIN')
MAKERDAO_TUSD_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_TUSD_A_JOIN')
MAKERDAO_ZRX_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_ZRX_A_JOIN')
MAKERDAO_PAXUSD_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_PAXUSD_A_JOIN')
MAKERDAO_COMP_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_COMP_A_JOIN')
MAKERDAO_LRC_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_LRC_A_JOIN')
MAKERDAO_LINK_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_LINK_A_JOIN')
MAKERDAO_BAL_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_BAL_A_JOIN')
MAKERDAO_YFI_A_JOIN = lambda: EthereumConstants().contract('MAKERDAO_YFI_A_JOIN')

MAKERDAO_CAT = lambda: EthereumConstants().contract('MAKERDAO_CAT')
MAKERDAO_JUG = lambda: EthereumConstants().contract('MAKERDAO_JUG')

YEARN_YCRV_VAULT = lambda: EthereumConstants().contract('YEARN_YCRV_VAULT')
YEARN_3CRV_VAULT = lambda: EthereumConstants().contract('YEARN_3CRV_VAULT')
YEARN_DAI_VAULT = lambda: EthereumConstants().contract('YEARN_DAI_VAULT')
YEARN_WETH_VAULT = lambda: EthereumConstants().contract('YEARN_WETH_VAULT')
YEARN_YFI_VAULT = lambda: EthereumConstants().contract('YEARN_YFI_VAULT')
YEARN_ALINK_VAULT = lambda: EthereumConstants().contract('YEARN_ALINK_VAULT')
YEARN_USDT_VAULT = lambda: EthereumConstants().contract('YEARN_USDT_VAULT')
YEARN_USDC_VAULT = lambda: EthereumConstants().contract('YEARN_USDC_VAULT')
YEARN_TUSD_VAULT = lambda: EthereumConstants().contract('YEARN_TUSD_VAULT')
YEARN_GUSD_VAULT = lambda: EthereumConstants().contract('YEARN_GUSD_VAULT')
YEARN_BCURVE_VAULT = lambda: EthereumConstants().contract('YEARN_BCURVE_VAULT')
YEARN_SRENCURVE_VAULT = lambda: EthereumConstants().contract('YEARN_SRENCURVE_VAULT')

ETH_SCAN = lambda: EthereumConstants().contract('ETH_SCAN')
ETH_MULTICALL = lambda: EthereumConstants().contract('ETH_MULTICALL')


AAVE_LENDING_POOL = lambda: EthereumConstants().contract('AAVE_LENDING_POOL')

ATOKEN_ABI = lambda: EthereumConstants.abi('ATOKEN')
ZERION_ABI = lambda: EthereumConstants.abi('ZERION_ADAPTER')
CTOKEN_ABI = lambda: EthereumConstants.abi('CTOKEN')
ERC20TOKEN_ABI = lambda: EthereumConstants.abi('ERC20_TOKEN')
FARM_ASSET_ABI = lambda: EthereumConstants.abi('FARM_ASSET')

YEARN_VAULTS_PREFIX = 'yearn_vaults_events'
