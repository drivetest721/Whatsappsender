import asyncio
from playwright.async_api import async_playwright, expect
import os
import re

async def send_whatsapp_message(dictMessageData):
    cookie_file = 'state.json'

    async with async_playwright() as p:
        # Launch the browser in persistent mode to avoid logging out
        user_data_dir = "user_data"
        chromium_args = [
            "--disable-blink-features=AutomationControlled",  # Disables the automation detection
            "--disable-infobars",  # Disables the "Chrome is being controlled by automated software" banner
        ]
        
        if os.path.exists(cookie_file):
            # Persistent context to retain login session
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=chromium_args,
            )
            print("Using existing state")
        else:
            browser = await p.chromium.launch(headless=False, args=chromium_args)  # Launch with anti-detection flags
            context = await browser.new_context()
            print("Creating new state")

        # Open WhatsApp Web
        page = await context.new_page()
        await page.goto('https://web.whatsapp.com')

        # If no cookie file exists, wait for manual login
        if not os.path.exists(cookie_file):
            print("Waiting for manual login...")
            await page.wait_for_timeout(30000)  # Wait for 30 seconds for manual login
            # Save cookies after login
            await context.storage_state(path="state.json")
            print("State saved for future sessions.")

        # Wait until WhatsApp Web fully loads (adjust the timeout if necessary)
        await page.wait_for_timeout(10000)

        # Check if WhatsApp is still logged in
        try:
            await expect(page.get_by_role("button", name="New chat", exact=True)).to_be_visible()
            print("WhatsApp is logged in")
        except:
            print("WhatsApp is not logged in, please log in manually.")

        # Start a new chat
        for phoneNo, dictData in dictMessageData.items():
            await page.get_by_role("button", name="New chat", exact=True).click()
            
            # Search for the phone number or name
            await page.get_by_role("textbox").first.fill(str(phoneNo))

            
            # Wait for search results to load
            await page.wait_for_selector('role=listitem')  # Wait until at least one list item appears

            # Select the second list item that appears in the search results
            await page.get_by_role("listitem").nth(1).click()  # Index is 0-based, so nth(1) selects the second item

            # Continue with sending the message
            await page.locator("#main").get_by_role("paragraph").type(dictData["message"], delay=1000)  # wait for 1 second delay after typing one character
            # Click the "Send" button
            await page.get_by_label("Send").first.click() # to send the message
           
            # Set input files with a delay between each file
            for file_path in dictData["attachments"]:
                await page.locator('input[type="file"]').first.set_input_files(file_path)
                await page.wait_for_timeout(1000)  # Wait for 1 second before selecting the next file

            # Add a delay before clicking the "Send" button
            await page.wait_for_timeout(2000)  # Wait for 2 seconds before clicking send

            # Click the "Send" button
            await page.get_by_label("Send").first.click()

            await page.wait_for_timeout(10000)  # Wait for 2 seconds before clicking send

        # Close the browser
        await context.close()

# Usage

dictReceiverInfo = {
   
}
# Run the async function
asyncio.run(send_whatsapp_message(dictReceiverInfo))
