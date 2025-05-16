import asyncio
import aiohttp


async def send_request():
    url = 'http://att.targetedproxies.com:11505/selling/generate?token=a121eaa3dbfd4fef8384dbb8bd1e8278'
    headers = {'Content-Type': 'application/json'}
    data = {
        "positionFrom": 1, "positionTo": 2, "numberOfPorts": 2, "authMethod": 0,
        "authEntry": "",
        "userAuthenticationEntry": "r5scjq:klinbk", "portType": 1, "ipType": 1, "genPort": 2,
        "genPortStart": 20001, "expiredDate": 1628964354656, "counterUploadLimit": 0, "counterUploadLimitBy": 1,
        "counterUploadQuotaInMB": 100, "counterDownloadLimit": 0, "counterDownloadLimitBy": 1,
        "counterDownloadQuotaInMB": 100, "counterAllLimit": 1, "counterAllLimitBy": 1, "counterAllQuotaInMB": 1000,
        "bwLimitEnabled": 0, "bwLimitRate": 0, "customDNS": "8.8.8.8 8.8.4.4",
        "maxConnection": 1000, "memo": "Test"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                print(f"Response status: {response.status}")
                print(f"Response content: {await response.text()}")
            else:
                print(f"Error: {response.status} - {await response.text()}")


asyncio.run(send_request())

