import json
from os import getenv
import requests
from watcher.config import RPC
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
ARBISCAN_API_KEY = getenv("ARBISCAN_API_KEY")
QUERY_URI = 'https://api.arbiscan.io/api?module=contract&action=getabi&address='
w3 = Web3(Web3.HTTPProvider(RPC.arbitrum.events.https))

class BlockExplorer:
    def __init__(self):
        pass

    def get_abi(self, contractAddress):
        url = (
            QUERY_URI
            + contractAddress
            + "&apikey="
            + ARBISCAN_API_KEY
        )

        data = requests.get(url).json()
        if data['status'] != '1':
            return None
        
        contractABI = json.loads(data['result'])
        return contractABI
    
if __name__ == '__main__':
    print(BlockExplorer().get_abi('0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9x'))