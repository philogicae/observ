class PROMPTS:
    default = """You are an AI assistant ready to answer to any question."""
    analyse = """In the context of blockchain on-chain activity analysis and given an user instruction, identify the request intention, the contract address, if it's a ERC20 token (decimals field populated by a boolean), and the condition (if none, leave it empty). If the address is missing or isn't a valid checksum address (0x...), ALWAYS leave it empty. Never comment or explain, ONLY respond with a valid formatted JSON.
# Examples:
- Input 1:
#tellmewhen someone is minting an NTF 0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f
- Output 1:
{"intention": "Detect NTF minting", "address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f", "decimals": false, "condition": ""}
- Input 2:
#tellmewhen someone is moving more than 1 WBTC 0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f
- Output 2:
{"intention": "Detect WBTC transfer", "address": "", "decimals": true, "condition": "Amount > 1 WBTC"}"""
    method = """In the context of blockchain on-chain activity analysis, only given an user intention and an contract ABI, identify the specific event name to listen. Never comment or explain, ONLY respond with a valid formatted JSON including the event name.:
Example:
{"event": "Transfer"}"""
    condition = """In the context of blockchain on-chain activity analysis, only given an user intention, a condition (it can be none) and some eth logs, ONLY return relevant events if there is some. Never comment or explain, ONLY respond with a valid formatted JSON:
Example of no relevant event:
{"found": []}
Example of few relevant events:
{"found": [{"from": "0xC6962004f452bE9203591991D15f6b388e09E8D0", "to":
"0x75010B38696E3045072Ea8bEbAbEE8E4b8A3706C", "value": 2684610564}, {"from": "0xf7e96217347667064DEE8f20DB747B1C7df45DDe", "to":
"0x01A3c8E513B758EBB011F7AFaf6C37616c9C24d9", "value": 2979000}]}"""
