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
