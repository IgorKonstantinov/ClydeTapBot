import asyncio
import hmac
import hashlib
import pprint
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
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            self.user_id = (await self.tg_client.get_me()).id

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

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

    async def login(self, http_client: aiohttp.ClientSession, user_data):
        try:
            data = user_data
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

    async def boosts(self, http_client: aiohttp.ClientSession, coins: int = 0, action: str = '') -> bool:
        try:
            match action:
                case 'energy-turbo':
                    boosts_url = f"https://api.clydetap.site/api/user/{self.user_id}/energy-turbo/update"
                    response = await http_client.post(url=boosts_url, json={'coins': coins})

                case 'boost_turbo':
                    boosts_url = f"https://api.clydetap.site/api/user/{self.user_id}/turbo/update"
                    response = await http_client.post(url=boosts_url, json={'coins': coins})

                case 'multi-tap':
                    boosts_url = f"https://api.clydetap.site/api/user/{self.user_id}/multi-tap/update"
                    response = await http_client.post(url=boosts_url, json={'coins': coins})

                case 'restore-energy':
                    boosts_url = f"https://api.clydetap.site/api/user/{self.user_id}/restore/energy"
                    response = await http_client.post(url=boosts_url)

                case 'active_day_bonus':
                    boosts_url = f"https://api.clydetap.site/api/user/{self.user_id}/bonus"
                    response = await http_client.post(url=boosts_url)

            response.raise_for_status()
            return True

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Boost {action}: {error} ")
            await asyncio.sleep(delay=30)
            return False

    # async def boost_energy_turbo(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
    #     try:
    #         boost_energy_turbo_url = f"https://api.clydetap.site/api/user/{user}/energy-turbo/update"
    #         response = await http_client.post(url=boost_energy_turbo_url, json={'coins': coins})
    #         response.raise_for_status()
    #         return True
    #
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error when Apply energy-turbo-boost {coins} coins: {error} ")
    #         await asyncio.sleep(delay=30)
    #         return False

    # async def boost_turbo(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
    #     try:
    #         boost_turbo_url = f"https://api.clydetap.site/api/user/{user}/turbo/update"
    #         response = await http_client.post(url=boost_turbo_url, json={'coins': coins})
    #         response.raise_for_status()
    #         return True
    #
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error when Apply turbo-boost {coins} coins: {error}")
    #         await asyncio.sleep(delay=30)
    #         return False

    # async def boost_multi_tap(self, http_client: aiohttp.ClientSession, coins: int, user: int) -> bool:
    #     try:
    #         boost_multi_tap_url = f"https://api.clydetap.site/api/user/{user}/multi-tap/update"
    #         response = await http_client.post(url=boost_multi_tap_url, json={'coins': coins})
    #         response.raise_for_status()
    #         return True
    #
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error when Apply multi_tap-boost {coins} coins: {error}")
    #         await asyncio.sleep(delay=30)
    #         return False

    # async def boost_restore_energy(self, http_client: aiohttp.ClientSession, user: int) -> bool:
    #     try:
    #         boost_restore_energy_url = f"https://api.clydetap.site/api/user/{user}/restore/energy"
    #         response = await http_client.post(url=boost_restore_energy_url)
    #         response.raise_for_status()
    #         return True
    #
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error when Apply boost_restore_energy: {error}")
    #         await asyncio.sleep(delay=30)
    #         return False
    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        tg_web_data = await self.get_tg_web_data(proxy=proxy)
        tg_web_data_parts = tg_web_data.split('&')
        query_id = tg_web_data_parts[0].split('=')[1]
        user_data = tg_web_data_parts[1].split('=')[1]
        auth_date = tg_web_data_parts[2].split('=')[1]
        hash_value = tg_web_data_parts[3].split('=')[1]

        while True:
            try:
                #Randomize variables
                random_sleep = random.randint(*settings.SLEEP_RANDOM)
                long_sleep = random.randint(*settings.SLEEP_LONG)

                if not tg_web_data:
                    continue

                if http_client.closed:
                    proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
                    http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)

                if time() - access_token_created_time >= 3600:
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    tg_web_data_parts = tg_web_data.split('&')
                    user_data = tg_web_data_parts[1].split('=')[1]

                    access_token_created_time = time()
                    http_client.headers["init-data"] = tg_web_data

                player_data = await self.login(http_client=http_client, user_data=user_data)

                player_username = player_data['data']['username']
                player_coins = player_data['data']['coins']
                player_coins_per_tap = player_data['data']['coins_per_tap']
                player_collected_coins = player_data['data']['collected_coins']

                player_energy = player_data['data']['energy']
                player_energy_limit = player_data['data']['energy_limit']

                player_active_day_bonus = player_data['data']['active_day_bonus']

                #boost
                player_boost_restore_energy = player_data['data']['boost']['restore_energy']['can_update']

                player_boost_energy_turbo = player_data['data']['boost']['energy_turbo']['can_update']
                player_boost_energy_turbo_coins = player_data['data']['boost']['energy_turbo']['coins']

                player_boost_turbo = player_data['data']['boost']['turbo']['can_update']
                player_boost_turbo_coins = player_data['data']['boost']['turbo']['coins']

                player_boost_multi_tap = player_data['data']['boost']['multi_tap']['can_update']
                player_boost_multi_tap_coins = player_data['data']['boost']['multi_tap']['coins']
                player_boost_multi_tap_time = player_data['data']['multi_tap']

                logger.info(f"{self.session_name} | Login:  | "
                            f"Player: <g>{player_username}</g> | Coins: Total <c>{player_coins:,}</c> Collected <c>{player_collected_coins:,}</c> | Energy: <e>{player_energy:,}/{player_energy_limit:,}</e>")

                logger.success(f"{self.session_name} | Boosts: | "
                               f"restore_energy: {player_boost_restore_energy} | energy_turbo {player_boost_energy_turbo} (<c>{player_boost_energy_turbo_coins}</c> coins) | boost_turbo {player_boost_turbo} (<c>{player_boost_turbo_coins}</c> coins) Boost_multi_tap {player_boost_multi_tap} (<c>{player_boost_multi_tap_coins}</c> coins) last activated: <c>{player_boost_multi_tap_time} </c>")

                if not player_data:
                    continue

                 #BOOSTS
                if settings.APPLY_DAILY_BOOST:

                    if player_active_day_bonus:
                        boost_action = 'active_day_bonus'
                        logger.info(f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                        await asyncio.sleep(delay=random_sleep)

                        status = await self.boosts(http_client=http_client, action=boost_action)
                        if status is True:
                            logger.success(f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated")
                            await asyncio.sleep(delay=random_sleep)

                    if player_boost_energy_turbo:
                        boost_action = 'energy-turbo'
                        logger.info(f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                        await asyncio.sleep(delay=random_sleep)

                        status = await self.boosts(http_client=http_client, coins=player_boost_energy_turbo_coins, action=boost_action)
                        if status is True:
                            logger.success(f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated | "
                                           f"турбо майнинг, х2 восстановления энергии за 2 часа")
                            await asyncio.sleep(delay=random_sleep)

                    if player_boost_turbo:
                        boost_action = 'boost_turbo'
                        logger.info(f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                        await asyncio.sleep(delay=random_sleep)

                        status = await self.boosts(http_client=http_client, coins=player_boost_turbo_coins, action=boost_action)
                        if status is True:
                            logger.success(f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated | "
                                           f" майнинг, х2 прибыли в час на 1.5 часа")
                            await asyncio.sleep(delay=random_sleep)

                    if player_boost_multi_tap:
                        boost_action = 'multi-tap'
                        current_time = datetime.now(timezone.utc).timestamp()-7200
                        player_boost_multi_tap_time_formatted = datetime.strptime(player_boost_multi_tap_time, "%Y-%m-%d %H:%M:%SZ").timestamp()

                        if current_time - player_boost_multi_tap_time_formatted >= 3601:
                            logger.info(f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                            await asyncio.sleep(delay=random_sleep)

                            status = await self.boosts(http_client=http_client, coins=player_boost_multi_tap_coins,action=boost_action)
                            if status is True:
                                logger.success(f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated | "
                                               f"майнинг, х2 прибыли за тап в час")
                                await asyncio.sleep(delay=random_sleep)

                # if player_boost_restore_energy and player_energy < 1000:
                #     boost_action = 'restore-energy'
                #     logger.info(f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                #     await asyncio.sleep(delay=random_sleep)
                #
                #     status = await self.boosts(http_client=http_client, action=boost_action)
                #     if status is True:
                #         logger.success(f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated | "
                #                        f"Заполняет энергию до максимума")
                #         await asyncio.sleep(delay=random_sleep)

                    ### Taps
                logger.info(f"{self.session_name} | sleep {random_sleep:,}s before bot action: <e>[tap]</e>")
                await asyncio.sleep(delay=random_sleep)

                while player_energy > 100:
                    taps = random.randint(*settings.RANDOM_TAPS_COUNT)
                    taps_coins = taps * player_coins_per_tap

                    if taps_coins >= player_energy:
                        taps_coins = player_energy
                    taps_data = await self.task_mine(http_client=http_client, taps=taps_coins)

                    if taps_data:
                        player_energy -= taps_data['data']['energy']
                        tap_coins_total = taps_data['data']['coins']
                        tap_coins_per_tap = taps_data['data']['coins_per_tap']
                        tap_coins = taps * tap_coins_per_tap
                        tap_energy_limit = taps_data['data']['energy_limit']

                        logger.success(
                            f"{self.session_name} | Bot action: <red>[tap/{taps}]</red> | Coins: <c>[{tap_coins}/{tap_coins_total}]</c> Energy: <e> {player_energy:,}/{tap_energy_limit:,}</e>")
                        await asyncio.sleep(delay=random_sleep)
                    else:
                        logger.error(f"{self.session_name} | Bot action:[tap] error")

                    if player_boost_restore_energy and player_energy < (player_energy_limit / 10):
                        boost_action = 'restore-energy'
                        logger.info(
                            f"{self.session_name} | Sleep {random_sleep}s before activate <e>[{boost_action}]</e>")
                        await asyncio.sleep(delay=random_sleep)

                        status = await self.boosts(http_client=http_client, action=boost_action)
                        if status is True:
                            logger.success(
                                f"{self.session_name} | Boost <red>[{boost_action}]</red> successfully activated | "
                                f"Заполняет энергию до максимума")
                            player_energy = player_energy_limit
                            player_boost_restore_energy = False
                            await asyncio.sleep(delay=random_sleep)

                else:
                    logger.info(f"{self.session_name} | Minimum energy reached: <e>{player_energy}</e>")

                logger.info(f"{self.session_name} | Sleep {long_sleep:,}s")
                await asyncio.sleep(delay=long_sleep)

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
