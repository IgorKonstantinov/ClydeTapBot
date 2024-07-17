import asyncio
import hmac
import hashlib
import random
from urllib.parse import unquote, quote
from time import time
from datetime import datetime, timezone

import aiohttp
import json
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers

class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = 0
        self.username = None

    async def get_secret(self, userid):
        key_hash = str("adwawdasfajfklasjglrejnoierjboivrevioreboidwa").encode('utf-8')
        message = str(userid).encode('utf-8')
        hmac_obj = hmac.new(key_hash, message, hashlib.sha256)
        secret = str(hmac_obj.hexdigest())
        return secret

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('clydetapbot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    logger.info(f"{self.session_name} | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://web.clydetap.site/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(string= auth_url.split('user%3D', maxsplit=1)[1].split('%26auth_date', maxsplit=1)[0]))

            tg_web_data_json = json.loads(tg_web_data)

            self.user_id = (await self.tg_client.get_me()).id
            self.username = ''

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data_json

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=30)


    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")
            await asyncio.sleep(delay=30)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data):
        try:
            data = tg_web_data
            login_url = f"https://api.clydetap.site/api/user/{self.user_id}/per/hour"

            response = await http_client.post(url=login_url, data=data)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Login  Error: {error}")
            await asyncio.sleep(delay=30)

    async def task_mine(self, http_client: aiohttp.ClientSession, taps):
        try:
            json_data = { 'coins': taps, "energy": taps }
            task_url = f"https://api.clydetap.site/api/user/{self.user_id}/taped"

            response = await http_client.post(url=task_url, json=json_data)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply task_mine: {error}")
            await asyncio.sleep(delay=30)

    async def active_day_bonus(self, http_client: aiohttp.ClientSession, user: int ):
        try:
            active_day_bonus_url = f"https://api.clydetap.site/api/user/{user}/bonus"

            response = await http_client.post(url=active_day_bonus_url)
            response.raise_for_status()

            response_json = await response.json()
            return response_json

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply task_mine: {error} ")
            await asyncio.sleep(delay=30)

    async def boost_energy_turbo(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
        try:
            boost_energy_turbo_url = f"https://api.clydetap.site/api/user/{user}/energy-turbo/update"
            response = await http_client.post(url=boost_energy_turbo_url, json={'coins': coins})
            response.raise_for_status()
            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply energy-turbo-boost {coins} coins: {error} ")
            await asyncio.sleep(delay=30)
            return False

    async def boost_turbo(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
        try:
            boost_turbo_url = f"https://api.clydetap.site/api/user/{user}/turbo/update"
            response = await http_client.post(url=boost_turbo_url, json={'coins': coins})
            response.raise_for_status()
            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply turbo-boost {coins} coins: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def boost_multi_tap(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
        try:
            boost_multi_tap_url = f"https://api.clydetap.site/api/user/{user}/multi-tap/update"
            response = await http_client.post(url=boost_multi_tap_url, json={'coins': coins})
            response.raise_for_status()
            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply multi_tap-boost {coins} coins: {error}")
            await asyncio.sleep(delay=30)
            return False

    async def boost_restore_energy(self, http_client: aiohttp.ClientSession, user: int) -> bool:
        try:
            boost_restore_energy_url = f"https://api.clydetap.site/api/user/{user}/restore/energy"
            response = await http_client.post(url=boost_restore_energy_url)
            response.raise_for_status()
            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply boost_restore_energy: {error}")
            await asyncio.sleep(delay=30)
            return False
    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        tg_web_data = await self.get_tg_web_data(proxy=proxy)

        while True:
            try:
                if not tg_web_data:
                    continue

                if http_client.closed:
                    proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
                    http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)

                if time() - access_token_created_time >= 3600:
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    access_token_created_time = time()

                    player_data = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                    player_username = player_data['data']['username']
                    player_coins = player_data['data']['coins']
                    player_energy = player_data['data']['energy']
                    player_energy_limit = player_data['data']['energy_limit']

                    player_collected_coins = player_data['data']['collected_coins']

                    #boost
                    #player_boost_restore_energy = player_data['data']['boost']['restore_energy']['can_update']
                    #player_boost_restore_energy_time = player_data['data']['restore_energy_at']

                    #player_boost_energy_turbo = player_data['data']['boost']['energy_turbo']['can_update']
                    #player_boost_energy_turbo_coins = player_data['data']['boost']['energy_turbo']['coins']
                    #player_boost_energy_turbo_time = player_data['data']['energy_turbo_at']

                    #player_boost_turbo = player_data['data']['boost']['turbo']['can_update']
                    #player_boost_turbo_coins = player_data['data']['boost']['turbo']['coins']
                    #player_boost_turbo_coins_time = player_data['data']['turbo']

                    #player_boost_multi_tap = player_data['data']['boost']['multi_tap']['can_update']
                    #player_boost_multi_tap_coins = player_data['data']['boost']['multi_tap']['coins']
                    #player_boost_multi_tap_time = player_data['data']['multi_tap']

                    logger.success(f"{self.session_name} | Login ok! | "
                                   f"Player: <c> {player_username} </c> | Total Coins: <c>{player_coins:,}</c> Collected coins <c>{player_collected_coins:,} </c> | Energy: <e>{player_energy:,}</e>, Total: <e>{player_energy_limit:,}</e>")

                    #logger.success(f"{self.session_name} | Boosts | "
                    #               f"Boost_restore_energy: {player_boost_restore_energy} | boost_energy_turbo {player_boost_energy_turbo} (<c>{player_boost_energy_turbo_coins}</c> coins) | boost_turbo {player_boost_turbo} (<c>{player_boost_turbo_coins}</c> coins) Boost_multi_tap {player_boost_multi_tap} (<c>{player_boost_multi_tap_coins}</c> coins) last activated: <c>{player_boost_multi_tap_time} </c>")

                    if not player_data:
                        continue

                taps = random.randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                taps_data = await self.task_mine(http_client=http_client, taps=taps)

                tap_energy = taps_data['data']['energy']
                tap_energy_limit = taps_data['data']['energy_limit']
                tap_coins_total = taps_data['data']['coins']
                tap_coins_per_tap = taps_data['data']['coins_per_tap']
                tap_coins = taps * tap_coins_per_tap

                tap_active_day_bonus = taps_data['data']['active_day_bonus']

                # boost
                tap_boost_restore_energy = taps_data['data']['boost']['restore_energy']['can_update']
                # tap_boost_restore_energy_time = tap_data['data']['restore_energy_at']

                tap_boost_energy_turbo = taps_data['data']['boost']['energy_turbo']['can_update']
                tap_boost_energy_turbo_coins = taps_data['data']['boost']['energy_turbo']['coins']
                # tap_boost_energy_turbo_time = tap_data['data']['energy_turbo_at']

                tap_boost_turbo = taps_data['data']['boost']['turbo']['can_update']
                tap_boost_turbo_coins = taps_data['data']['boost']['turbo']['coins']
                # tap_boost_turbo_coins_time = tap_data['data']['turbo']

                tap_boost_multi_tap = taps_data['data']['boost']['multi_tap']['can_update']
                tap_boost_multi_tap_coins = taps_data['data']['boost']['multi_tap']['coins']
                tap_boost_multi_tap_time = taps_data['data']['multi_tap']

                logger.success(f"{self.session_name} | Successful tapped! | "
                               f" Taps: <b>{taps:,}</b>, Tapped coins: <d>{tap_coins:,}</d> Total Coins: <c>{tap_coins_total:,}</c> | Energy: Used: <e> {tap_energy:,}</e>, Total: <e>{tap_energy_limit:,}</e>")

                if settings.APPLY_DAILY_BOOST:
                    if tap_boost_energy_turbo:
                        logger.info(f"{self.session_name} | Sleep 5s before activate <e>boost_energy_turbo</e>")
                        await asyncio.sleep(delay=5)

                        status = await self.boost_energy_turbo(http_client=http_client, coins=tap_boost_energy_turbo_coins, user=self.user_id)
                        if status is True:
                            logger.success(f"{self.session_name} | boost_energy_turbo successfully activated | турбо майнинг, х2 восстановления энергии за 2 часа")
                            await asyncio.sleep(delay=1)

                        continue

                    if tap_active_day_bonus:
                        logger.info(f"{self.session_name} | Sleep 5s before activate <e>tap_active_day_bonus</e>")
                        await asyncio.sleep(delay=5)

                        status = await self.active_day_bonus(http_client=http_client,user=self.user_id)
                        if status is True:
                            logger.success(f"{self.session_name} | active_day_bonus successfully activated ")
                            await asyncio.sleep(delay=1)

                        continue

                    if tap_boost_turbo:
                        logger.info(f"{self.session_name} | Sleep 5s before activate <e>boost_turbo</e>")
                        await asyncio.sleep(delay=5)

                        status = await self.boost_turbo(http_client=http_client, coins=tap_boost_energy_turbo_coins,user=self.user_id)
                        if status is True:
                            logger.success(f"{self.session_name} | boost_turbo successfully activated | майнинг, х2 прибыли в час на 1.5 часа")
                            await asyncio.sleep(delay=1)

                        continue

                    if tap_boost_multi_tap:
                        current_time = datetime.now(timezone.utc).timestamp()-7200
                        tap_boost_multi_tap_time_formatted = datetime.strptime(tap_boost_multi_tap_time, "%Y-%m-%d %H:%M:%SZ").timestamp()
                        print(current_time - tap_boost_multi_tap_time_formatted)

                        if current_time - tap_boost_multi_tap_time_formatted >= 3601:
                            logger.info(f"{self.session_name} | Sleep 5s before activate <e>boost_multi_tap</e>")
                            await asyncio.sleep(delay=5)

                            status = await self.boost_multi_tap(http_client=http_client, coins=tap_boost_multi_tap_coins,user=self.user_id)
                            if status is True:
                                logger.success(f"{self.session_name} | boost_multi_tap successfully activated | майнинг, х2 прибыли за тап в час")
                                await asyncio.sleep(delay=1)
                                boost_multi_tap_time = time()
                            continue

                if tap_boost_restore_energy and tap_energy < 1000:
                    logger.info(f"{self.session_name} | Sleep 5s before activate <e>boost_restore_energy</e>")
                    await asyncio.sleep(delay=5)

                    status = await self.boost_restore_energy(http_client=http_client,user=self.user_id)
                    if status is True:
                        logger.success(
                            f"{self.session_name} | boost_restore_energy successfully activated | Заполняет энергию до максимума")
                        await asyncio.sleep(delay=1)

                    continue

                if tap_energy < settings.MIN_AVAILABLE_ENERGY:
                    random_sleep = random.randint(settings.SLEEP_BY_MIN_ENERGY[0], settings.SLEEP_BY_MIN_ENERGY[1])
                    logger.info(f"{self.session_name} | Minimum energy reached: {tap_energy}")
                    logger.info(f"{self.session_name} | Sleep {random_sleep:,}s")

                    await asyncio.sleep(delay=random_sleep)
                    await http_client.close()
                    access_token_created_time = 0

                else:
                    sleep_between_tap = random.randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])
                    logger.info(f"Sleep between tap:  {sleep_between_tap}s")
                    await asyncio.sleep(delay=sleep_between_tap)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=30)
                await http_client.close()
                access_token_created_time = 0


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
