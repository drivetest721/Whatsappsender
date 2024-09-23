import asyncio
import json
from LogManager import CLogger
import argparse
import os
from playwright.async_api import async_playwright, TimeoutError
# from playwright_stealth import stealth_async

class WhatsAppAutomation:
    def __init__(self, log_directory, csv_directory=None, user_data_dir="data"):
        if not user_data_dir:
            user_data_dir = "data"
        self.logger = CLogger(log_directory, csv_directory)
        self.user_data_dir = user_data_dir

    async def execute_operations(self, page, operations, context_data):
        bMessageSent = False
        bAttachmentsAdded = False
        for operation in operations:
            try:
                action = operation['action']
                selector = operation.get('selector')
                index = operation.get('index', 0)  # Default to the first element if not specified

                if action == "conditional_click":
                    condition_selector = operation.get('condition_selector')
                    condition_selector_index = operation.get('condition_selector_index', 0)
                    true_selector = operation.get('true_selector')
                    false_selector = operation.get('false_selector')
                    fallback_selector = operation.get('fallback_selector')
                    true_index = operation.get('true_index', 0)  # Default to index 0 for true_selector
                    false_index = operation.get('false_index', 1)  # Default to index 1 for false_selector
                    
                    # try:
                    # If condition_selector is found, use true_selector and true_index
                    if await page.locator(condition_selector).count() > 0:
                        await page.locator(true_selector).nth(true_index).click()
                        self.logger.log_info(f"Condition met, clicked on true_selector: {true_selector} with index {true_index}")
                    else:
                        await page.locator(false_selector).nth(false_index).click()
                        self.logger.log_info(f"Condition not met, clicked on false_selector: {false_selector} with index {false_index}")
                    # except Exception as e:
                    #     # Fallback if something goes wrong
                    #     self.logger.log_error("conditional_click", "selector", f"Condition failed. Using fallback: {fallback_selector}")
                    #     await page.locator(fallback_selector).nth(true_index).click()

                elif action == "wait_for_selector":
                    await page.wait_for_selector(selector, timeout=operation.get('timeout', 10000))
                    self.logger.log_info(f"Waited for selector: {selector}")
                elif action == "click":
                    await page.locator(selector).nth(index).click()
                    self.logger.log_info(f"Clicked on selector: {selector}")
                elif action == "fill":
                    value = context_data[operation['value'].strip("{{").strip("}}")]
                    await page.fill(selector, value)
                    self.logger.log_info(f"Filled selector: {selector} with value: {value}")
                elif action == "clear":
                    await page.locator(selector).nth(index).clear()
                    self.logger.log_info(f"Cleared selector: {selector}")
                elif action == "type":
                    value = context_data[operation['value'].strip("{{").strip("}}")]
                    await page.locator(selector).nth(index).type(value, delay=operation.get('delay', 0))
                    self.logger.log_info(f"Typed in selector: {selector} with value: {value}")
                elif action == "attach_files":
                    files = context_data[operation['files'].strip("{{").strip("}}")]
                    if files:
                        await page.locator(selector).nth(index).set_input_files(files)
                        self.logger.log_info(f"Attached files to selector: {selector}")
                        bAttachmentsAdded = True
                    else:
                        self.logger.log_info(f"No files to be attached.")

                elif action == "sleep":
                    await asyncio.sleep(operation['duration'])
                    self.logger.log_info(f"Slept for {operation['duration']} seconds")

                elif action == "logcsv":
                    message_sent = operation.get("message_sent", None)  # User is saying that message is sent or not
                    attachments_sent = operation.get("attachments_sent", None) # User is saying that attachments are added or not
                
                    if message_sent and attachments_sent:
                        self.logger.log_to_csv(context_data["phoneNo"], bMessageSent, bAttachmentsAdded)
                    elif message_sent:
                        bMessageSent = True
                        self.logger.log_to_csv(context_data["phoneNo"], bMessageSent, bAttachmentsAdded)
                        
            except Exception as e:
                self.logger.log_error(action, selector, e)
                return 

    async def send_whatsapp_message(self, dictMessageData, browser_type="chromium", close_after_minutes=2, resource_directory=None):
        async with async_playwright() as p:
            # Define different args for Chromium, Firefox, and WebKit
            chromium_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
            
            # Choose the browser and launch with appropriate args
            if browser_type.lower() == "chromium":
                context = await p.chromium.launch_persistent_context(
                    args=chromium_args,
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    timeout=120000
                )
                page = await context.new_page()

            elif browser_type.lower() == "firefox":
                context = await p.firefox.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    timeout=120000
                )
                # Get the first page in the context instead of creating a new one
                try:
                    pages = context.pages
                    if len(pages) > 0:
                        page = pages[0]  # Use the first page that opens in the persistent context
                    else:
                        page = await context.new_page()  # Fallback in case no page is open
                except Exception as e:
                    page = await context.new_page()  # Fallback in case no page is open
                
                # Wait for the page to fully load
                await page.wait_for_load_state('load')  # 'load' ensures the full load of the page
                await page.bring_to_front()
                
            elif browser_type.lower() == "webkit":
                context = await p.webkit.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=False,
                    timeout=120000
                )
                page = await context.new_page()

            else:
                print("Please specify browsers from ('chromium', 'firefox', 'webkit')")
                raise ValueError(f"Unsupported browser type: {browser_type}")


            # page = await context.new_page()
            # await stealth_async(page)  # Apply stealth mode
            await page.goto('https://web.whatsapp.com', timeout=120000)

            try:
                # Set default resource directory if not provided
                if resource_directory is None:
                    resource_directory = os.path.dirname(os.path.abspath(__file__))  # Parallel to the .exe or .py file

                # Path to the sitesConfig.json file
                sites_config_path = os.path.join(resource_directory, 'sitesConfig.json')

                # Load the operations from the JSON structure
                with open(sites_config_path, 'r') as f:
                    json_data = json.load(f)
                    operations = json_data['sites']['whatsapp']['operations']

                # Iterate through each recipient
                for phoneNo, dictData in dictMessageData.items():
                    context_data = {
                        "phoneNo": phoneNo,
                        "message": dictData["message"],
                        "attachments": dictData["attachments"]
                    }
                    await self.execute_operations(page, operations, context_data)

                # Wait for the specified number of minutes before closing the browser
                if close_after_minutes > 0:
                    await asyncio.sleep(close_after_minutes * 60)  # Convert minutes to seconds

            except TimeoutError:
                self.logger.log_error("Login", "WhatsApp", "Failed to login to WhatsApp.")
            finally:
                # Close the context (and the browser) after completion
                await context.close()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Automation for sending WhatsApp messages.")
    parser.add_argument('--browser', type=str, required=False, default="chromium", help="Browser type (e.g., 'chromium', 'firefox', 'webkit')")
    parser.add_argument('--service', type=str, required=True, help="Service name (e.g., 'whatsapp')")
    parser.add_argument('--metadata_directory', type=str, help="Directory for saving cookies and session data.")
    parser.add_argument('--log_directory', type=str, required=True, help="Directory for saving logs.")
    parser.add_argument('--csv_directory', type=str, required=False, help="Optional: Directory for saving CSV logs.")
    parser.add_argument('--resource_directory', type=str, required=False, help="Optional: Directory for saving CSV logs.")

    parser.add_argument('--close_after_minutes', type=int, default=0, help="Number of minutes to keep the browser open after operations.")

    # Either JSON file or inline JSON data must be provided
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--data_path', type=str, help="JSON file containing the message data.")
    group.add_argument('--json_data', type=str, help="Inline JSON data for the message.")

    # Parse arguments
    args = parser.parse_args()

    # Load message data from the JSON file or inline JSON string
    if args.data_path:
        with open(args.data_path, 'r') as f:
            dictReceiverInfo = json.load(f)
    elif args.json_data:
        dictReceiverInfo = json.loads(args.json_data)

    if args.service.lower() == "whatsapp":
        # Initialize the WhatsAppAutomation with the directories
        automation = WhatsAppAutomation(args.log_directory, args.csv_directory, args.metadata_directory)

        # Run the async function to send messages
        asyncio.run(automation.send_whatsapp_message(dictReceiverInfo, args.browser, args.close_after_minutes, args.resource_directory))

    else:
        print("We only support whatsapp service right now, please specify service as 'whatsapp' only")