from time import sleep

from addict import Dict
from web3 import Web3

import bot
from data.db import DB

from .config import RPC


class EventListener:
    delay = 3

    def __init__(self):
        self.w3 = Web3(Web3.WebsocketProvider(RPC.arbitrum.events.wss))
        self.db = DB()
        self.handler = bot.Notifier().handler

    def get_filter(self, block_id, watched=None):
        results = self.db.fetch("get_event_requests", 100)
        data = Dict(
            {
                r[0]: Dict(
                    request_id=r[0],
                    chat_id=r[1],
                    user_id=r[2],
                    event_name=r[6],
                    condition=r[8],
                    decimals=r[9],
                    intention=r[10],
                )
                for r in results
            }
        )
        requests = [[r[0], r[4], r[5], r[6]] for r in results]
        new_watched = set(map(lambda x: x[0], requests))
        if new_watched != watched:
            zipped = list(zip(*requests)) if requests else None
            if not zipped:
                return None, None, None, None, True
            request_ids, addrs, abis, evts = zipped
            contracts = [
                self.w3.eth.contract(address=address, abi=abi)
                for address, abi in zip(addrs, abis)
            ]
            events = [
                e
                for i, c in enumerate(contracts)
                for e in c.events
                if evts[i] == e.__name__
            ]
            addr_mapping = dict()
            for i, addr in enumerate(addrs):
                if addr not in addr_mapping:
                    addr_mapping[addr] = []
                addr_mapping[addr].append([request_ids[i], events[i]])
            block_filter = self.w3.eth.filter(
                dict(address=list(set(addrs)), fromBlock=block_id)
            )
            return new_watched, addr_mapping, block_filter, data, True
        return None, None, None, None, False

    def listen(self):
        block_id = self.w3.eth.get_block_number()
        watched, addr_mapping, block_filter, data = None, None, None, None
        while True:
            if watched:
                logs = block_filter.get_new_entries()
                to_check = []
                if len(logs) > 0:
                    for log in logs:
                        for request_id, event in addr_mapping[log.address]:
                            try:
                                to_check.append(
                                    [
                                        request_id,
                                        data[request_id],
                                        log["transactionHash"],
                                        event().process_log(log),
                                    ]
                                )
                            except:
                                pass
                if to_check:
                    block_id = logs[-1].blockNumber
                    self.handler(to_check)
                else:
                    block_id = self.w3.eth.get_block_number()
            sleep(self.delay)
            new_watched, new_addr_mapping, new_block_filter, new_data, updated = (
                self.get_filter(block_id, watched)
            )
            if updated:
                watched, addr_mapping, block_filter, data = (
                    new_watched,
                    new_addr_mapping,
                    new_block_filter,
                    new_data,
                )

    def start(self):
        try:
            bot.Log.debug("Listener: Started.")
            self.listen()
        except KeyboardInterrupt:
            bot.Log.debug("Killed by KeyboardInterrupt")
        except Exception as e:
            bot.Log.error(f"Error: {e}")


def start_event_listener():
    EventListener().start()
