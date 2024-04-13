from web3 import Web3
from config import RPC


w3_https = Web3(Web3.HTTPProvider(RPC.arbitrum.events.https))
w3_wss = Web3(Web3.WebsocketProvider(RPC.arbitrum.events.wss))
