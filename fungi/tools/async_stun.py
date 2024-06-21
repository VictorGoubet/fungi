import asyncio

import stun


async def async_get_ip_info() -> tuple:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, stun.get_ip_info)
