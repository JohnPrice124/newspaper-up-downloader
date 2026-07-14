import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# توکن‌ها را دقیقاً بین دو علامت ' ' قرار بده
TELEGRAM_SESSION = '1BJWap1sBu2XKWMT5SwprfeGaIfE1koAMWJXZJoBvWff4v0pf2WPk0R4U0g_20EnvjHu-dFw7fYQKMab_OOZGIX2dUtra7lXyNeaChV0Gpv1YG2MRAGDkwMpd5at6267VY2Qx8nX-VQ17J188CehJwVzXlt4rI6fw-Th6uoBEcmGC_9Ac3xkSsvMF422gTvL14QurSjvTa_BYWG7IJ2IUSz6vMNQJyzGYAryV0UmAWBA208lEyA5LN_Sk1QMdm63EVJeK8Ndh53bnJsZUh5J-3fbSBB2BAOQY6ytEWXu9diNptEd9rD_UCihIuGpdKLltvrwgBK6QZW_5MlZ_U0chnGYV-nqdItg='

CLIENT_ID = '322682178837-8otjk7ikh9g4p30ujalr5se1u4f40lgu.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REFRESH_TOKEN = '1//04Ez3eeAlSOcsCgYIARAAGAQSNwF-L9IrQPFdyMUTZ8Rv17e_RbFFtOK4rB9Nm2ntqfdombK6Eo17wyscbUgBOoS_-ZzLFHGhCAM'

TARGET_CHANNELS = ['favemags', 'dailynewspaper88', 'EPW_MAGAZINE', 'business_magazines', 'dailynewspaper88magzine', 'wmback']
DRIVE_FOLDER_ID = '15Vp0_f6BN_Ia_hsVE4xFqAXjRr-lnA0x' 

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

try:
    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    print("✅ احراز هویت گوگل درایو موفق بود.")
except Exception as e:
    print(f"❌ خطا در کلیدهای گوگل درایو: {e}")
    exit(1)

client = TelegramClient(StringSession(TELEGRAM_SESSION), API_ID, API_HASH)

def check_file_exists_in_drive(file_name):
    """بررسی اینکه آیا فایلی با این نام قبلاً در پوشه گوگل درایو آپلود شده است یا خیر"""
    try:
        # ایمن‌سازی نام فایل برای کوئری گوگل درایو
        safe_name = file_name.replace("'", "\\'")
        query = f"name = '{safe_name}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        return len(results.get('files', [])) > 0
    except Exception as e:
        print(f"⚠️ خطا در بررسی تکراری بودن فایل در درایو: {e}")
        return False

async def main():
    await client.start()
    print("✅ اتصال به تلگرام موفقیت‌آمیز بود.")
    
    # بررسی پیام‌های ۲۴ ساعت گذشته برای شکار جدیدترین‌ها
    time_limit = datetime.now(timezone.utc) - timedelta(days=1)
    
    for channel in TARGET_CHANNELS:
        print(f"\n🔍 در حال اسکن کانال: {channel}")
        try:
            async for message in client.iter_messages(channel, offset_date=time_limit, reverse=True):
                if message.document and message.document.mime_type == 'application/pdf':
                    file_name = message.document.attributes[0].file_name if message.document.attributes else "document.pdf"
                    
                    # گام حیاتی: اگر فایل از قبل در درایو باشد، اصلاً پردازش نمی‌شود
                    if check_file_exists_in_drive(file_name):
                        print(f"⏭️ فایل '{file_name}' قبلاً در گوگل درایو آپلود شده است. اسکیپ شد.")
                        continue
                        
                    print(f"📥 فایل جدید یافت شد. شروع دانلود: {file_name}")
                    file_path = await message.download_media()
                    print("✅ دانلود تمام شد. در حال انتقال به گوگل درایو شخصی...")
                    
                    try:
                        file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
                        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
                        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                        
                        print(f"✅ آپلود انجام شد. ID فایل: {uploaded_file.get('id')}")
                        
                    except Exception as e:
                        print(f"❌ خطا در آپلود فایل: {e}")
                    
                    finally:
                        if os.path.exists(file_path):
                            os.remove(file_path)
        except Exception as e:
            print(f"❌ خطا در دسترسی یا اسکن کانال {channel}: {e}")

with client:
    client.loop.run_until_complete(main())
