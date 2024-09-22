import asyncio
import json
from LogManager import CLogger
import argparse

from playwright.async_api import async_playwright, TimeoutError

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

                if action == "wait_for_selector":
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

    async def send_whatsapp_message(self, dictMessageData):
        async with async_playwright() as p:
            chromium_args = [
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                        ]
            context = await p.chromium.launch_persistent_context(
                args=chromium_args,
                user_data_dir=self.user_data_dir,
                headless=False,
                timeout=120000
            )

            page = await context.new_page()
            await page.goto('https://web.whatsapp.com', timeout=120000)

            try:
                # Load the operations from the JSON structure
                with open(r'resources\sitesConfig.json', 'r') as f:
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

            except TimeoutError:
                self.logger.log_error("Login", "WhatsApp", "Failed to login to WhatsApp.")
            # No need to close the context here

# if __name__ == "__main__":
#     log_directory = 'logs'
#     dictReceiverInfo = {
#         "+123123": {
#             "message": "This is another test message.",
#             "attachments": []
#         },
#         "+12313": {
#             "message": "This is a test message sent using automation software.",
#             "attachments": [
#                 r"c:\Users\OneDrive\Documents\Resume.pdf",
#                 r"c:\Users\OneDrive\Documents\My Web Sites\WebSite1\w-brand.png",
#                 r"c:\Users\Downloads\WhatsApp Image 2024-08-10 at 8.59.56 AM (1).jpeg"
#             ]
#         },
#     }

#     # Run the async function
#     automation = WhatsAppAutomation(log_directory)
#     asyncio.run(automation.send_whatsapp_message(dictReceiverInfo))

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Automation for sending WhatsApp messages.")
    parser.add_argument('--service', type=str, required=True, help="Service name (e.g., 'whatsapp')")
    parser.add_argument('--metadata_directory', type=str, help="Directory for saving cookies and session data.")
    parser.add_argument('--log_directory', type=str, required=True, help="Directory for saving logs.")
    parser.add_argument('--csv_directory', type=str, required=False, help="Optional: Directory for saving CSV logs.")
    
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
        asyncio.run(automation.send_whatsapp_message(dictReceiverInfo))

    else:
        print("We only support whatsapp service right now, please specify service as 'whatsapp' only")