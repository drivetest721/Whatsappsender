import os
import logging
import traceback
from datetime import datetime
import csv

class CLogger:
    def __init__(self, log_directory, csvFileDirectory=None):
        self.log_directory = log_directory

        if csvFileDirectory:
            self.csvFileDirectory = csvFileDirectory
        else:
            self.csvFileDirectory = self.log_directory

        self.setup_logging()

    def setup_logging(self):
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        
        log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
        log_path = os.path.join(self.log_directory, log_filename)
        logging.basicConfig(filename=log_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        
        csv_filename = datetime.now().strftime("%Y-%m-%d") + ".csv"
        self.csv_file_path = os.path.join(self.csvFileDirectory, csv_filename)


    def log_error(self, action, selector, e):
        logging.error(f"Error executing {action} on {selector}: {e} : {traceback.format_exc()}")

    def log_info(self, message):
        logging.info(message)


    def log_to_csv(self, phone_number, message_sent=None, attachments_sent=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entries = []
        headers = ["Timestamp", "Phone Number", "Message Sent", "Attachments Sent"]

        # Check if the file exists and read existing data
        if os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, mode='r', newline='') as csv_file:
                reader = csv.reader(csv_file)
                entries = list(reader)

                # Check if the first row contains headers
                if entries and entries[0] == headers:
                    entries = entries[1:]  # Remove the header row for processing
                else:
                    self.log_info(f"CSV file missing headers. Adding default headers.")
                    entries.insert(0, headers)

        # Check if the phone number already exists
        updated = False
        for entry in entries:
            if entry[1] == phone_number:
                if message_sent is not None:
                    entry[2] = str(message_sent)
                if attachments_sent is not None:
                    entry[3] = str(attachments_sent)
                updated = True
                break

        # If not updated, add a new entry
        if not updated:
            entries.append([timestamp, phone_number, str(message_sent), str(attachments_sent)])

        # Write the updated data back to the CSV, ensuring headers are added
        with open(self.csv_file_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            # Write headers if the file is new or missing headers
            if not os.path.exists(self.csv_file_path) or not entries[0] == headers:
                writer.writerow(headers)

            writer.writerows(entries)
