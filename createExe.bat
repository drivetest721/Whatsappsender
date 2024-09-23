echo Activating environment...
call "envAutomation\Scripts\activate.bat"
echo Environment activated successfully.

echo Converting .py into .exe file

pyinstaller --noconfirm --onedir --console --name "WhatsappSender" --path "envAutomation\Lib\site-packages" --exclude-module "*.bak" "SourceCode\WhatsappSender.py" --add-data "resources;resources"
echo Successfully created envInvoiceDownload executable folder 