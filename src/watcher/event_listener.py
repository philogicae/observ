from addict import Dict
from web3 import Web3
from .config import RPC
import asyncio
from datetime import datetime
from rich import print


class EventListener:
    delay = 2

    def __init__(self, db, handler):
        self.w3 = Web3(Web3.WebsocketProvider(RPC.arbitrum.events.wss))
        self.db = db
        self.handler = handler

    def get_filter(self, block_id, watched=None):
        results = self.db.fetch("get_event_requests")
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
        zipped = list(zip(*requests))
        new_watched = set(map(lambda x: x[0], requests))
        if new_watched and new_watched != watched:
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
            return new_watched, addr_mapping, block_filter, data
        return None, None, None, None

    def listen(self):
        async def block_loop():
            block_id = self.w3.eth.get_block_number()
            watched, addr_mapping, block_filter, data = self.get_filter(block_id)
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
                        print(
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            + f" - At block {block_id}: No new log"
                        )
                else:
                    print(
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + f" - Nothing to watch"
                    )
                await asyncio.sleep(self.delay)
                new_watched, new_addr_mapping, new_block_filter, new_data = (
                    self.get_filter(block_id, watched)
                )
                if new_watched:
                    watched, addr_mapping, block_filter, data = (
                        new_watched,
                        new_addr_mapping,
                        new_block_filter,
                        new_data,
                    )

        async def task():
            await asyncio.gather(block_loop())

        try:
            asyncio.run(task())
        except KeyboardInterrupt:
            pass
