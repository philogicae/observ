from os import getenv

from addict import Dict
from dotenv import load_dotenv

load_dotenv()
blastapi_key = getenv("BLASTAPI_API_KEY")
alchemy_key = getenv("ALCHEMY_API_KEY")

RPC = Dict(
    arbitrum=Dict(
        events=Dict(
            https=f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
            wss=f"wss://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
        ),
        calls=Dict(
            https=f"https://arbitrum-one.blastapi.io/{blastapi_key}",
            wss=f"wss://arbitrum-one.blastapi.io/{blastapi_key}",
        ),
    )
)
