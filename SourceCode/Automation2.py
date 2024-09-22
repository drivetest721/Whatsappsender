import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import logging
import traceback
logging.basicConfig(filename="log.csv", level=logging.INFO)

async def send_whatsapp_message(dictMessageData):

    async with async_playwright() as p:
        user_data_dir = "data"
        chromium_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
        ]
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=chromium_args,
        )
        
        page = await context.new_page()
        await page.goto('https://web.whatsapp.com')

        # Ensure WhatsApp is loaded and logged in
        try:
            # Correct the selector syntax and ensure the element is visible
            await page.wait_for_selector('div[role="button"][title="New chat"]', timeout=120000)
            logging.info("WhatsApp is logged in.")
        except TimeoutError:
            logging.warning("Failed to login to whatsapp.")
            return

        # Iterate through each recipient
        for phoneNo, dictData in dictMessageData.items():
            try:
                # Start a new chat
                await page.locator('div[role="button"][title="New chat"]').click()
                await page.fill('div[role="textbox"] >> p', phoneNo, timeout=5000)

                # Wait for search results and select the contact
                await page.locator('div[role="listitem"]').nth(1).click()

                await page.locator('div[aria-placeholder="Type a message"]').clear()
                await page.locator('div[aria-placeholder="Type a message"]').type(dictData["message"], delay=100)

                # Click send button
                await page.locator('button[aria-label="Send"]').click()

                logging.info(f"Message sent to {phoneNo}")

                # Attach files, if any
                if dictData["attachments"]:
                    # await page.wait_for_selector('div[title="Attach"]', timeout=10000)
                    await page.locator('div[title="Attach"]').click()

                    await page.locator('div[id="main"] >> footer >> span:has-text("Document") + input').nth(0).set_input_files(dictData["attachments"])

                    # Send after attaching files
                    await page.locator('div[role="button"][aria-label="Send"]').click()

                    # await page.locator('span[data-testid="send"]').click()
                    logging.info(f"Files attached for {phoneNo}")

                await asyncio.sleep(5)  # Wait before sending to the next contact
            except Exception as e:
                logging.error(f"Error sending message to {phoneNo}: {e} : {traceback.print_exc()}")
                continue  # Continue with the next contact

        await context.close()

if __name__ == "__main__":

    # Usage example
    dictReceiverInfo = {}
    
    # Run the async function
    asyncio.run(send_whatsapp_message(dictReceiverInfo))
