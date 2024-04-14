# Observ: AI-Powered Telegram Assistant for easy & modular web3 notifications

Observ is a Telegram AI virtual assistant designed to help you easily set up notifications on EVM blockchains. Our solution provides an easy, personalized, and modular web3 notification setup, powered by AI.

## Example of use-cases:

Custom alerts for:
- USDC transfer higher than 1M USD.
- Mint of a given NFT.
- Monitor your health factor on Aave.

## Solution:

1. Open the Telegram bot: [Observ Telegram Bot](https://t.me/observonchainbot).
2. The bot will ask the user what notification they want to set up.
   - Chain (for the PoC, we currently only support Arbitrum).
   - Contract Address.
   - Desired Notification.
3. The user's intention is cast into a data structure (JSON with "intention", "condition", and "address") using LLM. If any elements are missing, the bot will prompt the user to provide them.
4. The bot calls the ArbiScan API to fetch the Contract ABI.
5. If the contract is a proxy, the implementation ABI is fetched.
6. The bot determines from the ABI which method or event could trigger the notification using LLM and creates a request.
7. The request is saved in a database, which is monitored in real-time by the 'watcher' bot.
   - If the request type is an event, the 'watcher' bot listens continuously to incoming events/logs via RPC websocket with a filter.
   - If the request type is a method, the 'watcher' bot calls it periodically through a call scheduler.
8. When an event is detected, LLM 'Notifier bot' checks if it meets the condition (if there is one).
   - If the request condition is met, the notifier bot generates a message to notify the user in their Telegram chatroom.
9. On our current implementation, a user can schedule multiple alerts, and the 'watcher' bot will pick them up. Our bots are deployed using Aleph IM decentralized cloud (VMs).

## Architecture schema:

![Alt text](/assets/observ-schema.png "Optional title")

## To expand our capabilities:

- Support other EVM blockchains.
- Events could trigger actions: generate transaction data -> create a URL link that redirects to a page allowing you to sign and send the transaction.
- Scraping the contract addresses instead of asking for them.
- Scalability on Indexing and Monitoring modules.
