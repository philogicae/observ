from os import getenv

from dotenv import load_dotenv
from requests import get

load_dotenv()
ARBISCAN_API_KEY = getenv("ARBISCAN_API_KEY")
URI_ABI = "https://api.arbiscan.io/api?module=contract&action=getabi"


class BlockExplorer:
    @staticmethod
    def get_abi(contractAddress):
        url = f"{URI_ABI}&address={contractAddress}&apikey={ARBISCAN_API_KEY}"
        try:
            return get(url).json()["result"]
        except:
            pass
