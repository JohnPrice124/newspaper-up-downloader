import os
import json
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# خواندن کلیدها از محیط امن گیت‌هاب
TELEGRAM_SESSION = os.environ.get('TELEGRAM_SESSION')
MAKE_WEBHOOK = os.environ.get('MAKE_WEBHOOK')

# 🛑 لیست کانال‌های شما مستقیماً جایگذاری شد 🛑
TARGET_CHANNELS = ['wmback', 'EPW_MAGAZINE', 'business_magazines', 'allmagss', 'dailynewspaper88magzine', 'dailynewspaper88']

# 🛑 فقط این یک مورد را با آیدی پوشه خود که در بالا توضیح دادم جایگزین کنید 🛑
DRIVE_FOLDER_ID = '15Vp0_f6BN_Ia_hsVE4xFqAXjRr-lnA0x' 

# کلیدهای عمومی تلگرام دسکتاپ
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

# احراز هویت گوگل درایو
try:
    credentials_dict = json.loads(os.environ.get('GDRIVE_CREDENTIALS'))
    credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes=['https://www.googleapis.com/auth/drive'])
    drive_service = build('drive', 'v3', credentials=credentials)
    print("✅ احراز هویت گوگل درایو موفق بود.")
except Exception as e:
    print(f"❌ خطا در کلیدهای گوگل درایو: {e}")
    exit(1)

# راه‌اندازی کلاینت تلگرام
client = TelegramClient(StringSession(TELEGRAM_SESSION), API_ID, API_HASH)

async def main():
    await client.start()
    print("✅ اتصال به تلگرام موفقیت‌آمیز بود.")
    
    # جستجو در پیام‌های 24 ساعت گذشته
    time_limit = datetime.now(timezone.utc) - timedelta(days=1)
    
    # چرخش روی تمام کانال‌های ارسالی شما
    for channel in TARGET_CHANNELS:
        print(f"\n🔍 در حال اسکن کانال: {channel}")
        try:
            async for message in client.iter_messages(channel, offset_date=time_limit, reverse=True):
                if message.document and message.document.mime_type == 'application/pdf':
                    file_name = message.document.attributes[0].file_name if message.document.attributes else "document.pdf"
                    print(f"📥 فایل یافت شد. شروع دانلود: {file_name}")
                    
                    # دانلود فایل
                    file_path = await message.download_media()
                    print("✅ دانلود تمام شد. در حال انتقال به گوگل درایو...")
                    
                    # آپلود در گوگل درایو
                    try:
                        file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
                        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                        
                        print(f"✅ آپلود انجام شد. ID فایل: {uploaded_file.get('id')}")
                        
                        # ارسال سیگنال به Make.com
                        payload = {
                            "file_name": file_name,
                            "drive_file_id": uploaded_file.get('id'),
                            "direct_download_link": f"https://drive.google.com/uc?export=download&id={uploaded_file.get('id')}"
                        }
                        response = requests.post(MAKE_WEBHOOK, json=payload)
                        
                        if response.status_code == 200:
                            print("🚀 سیگنال با موفقیت به Make ارسال شد.")
                        else:
                            print(f"⚠️ سیگنال ارسال شد اما Make ارور داد: {response.text}")
                            
                    except Exception as e:
                        print(f"❌ خطا در آپلود یا ارسال وب‌هوک: {e}")
                    
                    finally:
                        # پاک کردن فایل از سرور موقت برای جلوگیری از پر شدن فضا
                        if os.path.exists(file_path):
                            os.remove(file_path)
        except Exception as e:
            print(f"❌ خطا در دسترسی یا اسکن کانال {channel}: {e}")

with client:
    client.loop.run_until_complete(main())
