from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent
)
import json
import time
import hashlib
from typing import Dict, List

# تنظیمات ربات
class Config:
    API_ID = "11057906"
    API_HASH = "b7f975dcdf30c826b3e6178ff3f72356"
    BOT_TOKEN = "7812155764:AAF49wqPvcYt0ctDvzk2elSVaxF0nw-rRBw"
    
    # مدت زمان نگهداری پیام‌های نجوا (به ثانیه)
    WHISPER_TIMEOUT = 3600  # یک ساعت
    
    # حداکثر تعداد کاراکتر مجاز برای نجوا
    MAX_WHISPER_LENGTH = 200

class WhisperBot:
    def __init__(self):
        # ایجاد کلاینت ربات
        self.app = Client(
            "whisper_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        
        # دیکشنری برای ذخیره نجواها
        self.whispers: Dict[str, Dict] = {}
        
        # تنظیم هندلرها
        self.setup_handlers()

    def setup_handlers(self):
        # دستور شروع
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await message.reply_text(
                "👋 سلام! من ربات نجوا هستم.\n\n"
                "می‌توانید با استفاده از من پیام‌های خصوصی به افراد در گروه ارسال کنید.\n\n"
                "برای استفاده:\n"
                "1️⃣ مرا در گروه خود اضافه کنید\n"
                "2️⃣ در گروه، @botusername را تایپ کنید\n"
                "3️⃣ متن نجوا و گیرنده را مشخص کنید\n\n"
                "🔒 نجواها پس از خوانده شدن یا گذشت زمان مشخص، حذف می‌شوند."
            )

        # پردازش کوئری‌های inline
        @self.app.on_inline_query()
        async def handle_inline_query(client, inline_query: InlineQuery):
            query = inline_query.query
            
            if not query:
                # نمایش راهنما اگر کوئری خالی باشد
                await inline_query.answer(
                    results=[
                        InlineQueryResultArticle(
                            title="🤫 ایجاد نجوای جدید",
                            description="فرمت: متن نجوا | @username",
                            input_message_content=InputTextMessageContent(
                                "برای ایجاد نجوا، متن و نام کاربری گیرنده را وارد کنید.\n"
                                "مثال: سلام این یک پیام محرمانه است | @username"
                            ),
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("🔄 امتحان مجدد", switch_inline_query_current_chat="")
                            ]])
                        )
                    ],
                    cache_time=0
                )
                return

            # جداسازی متن نجوا و گیرنده
            parts = query.split("|", 1)
            if len(parts) != 2:
                await inline_query.answer(
                    results=[
                        InlineQueryResultArticle(
                            title="❌ فرمت نادرست",
                            description="لطفاً از فرمت صحیح استفاده کنید: متن | @username",
                            input_message_content=InputTextMessageContent(
                                "❌ فرمت نادرست. مثال صحیح:\n"
                                "سلام این یک پیام محرمانه است | @username"
                            )
                        )
                    ],
                    cache_time=0
                )
                return

            whisper_text, recipient = parts[0].strip(), parts[1].strip()
            
            # بررسی طول پیام
            if len(whisper_text) > Config.MAX_WHISPER_LENGTH:
                await inline_query.answer(
                    results=[
                        InlineQueryResultArticle(
                            title="❌ پیام طولانی",
                            description=f"حداکثر طول مجاز: {Config.MAX_WHISPER_LENGTH} کاراکتر",
                            input_message_content=InputTextMessageContent(
                                "❌ پیام شما طولانی‌تر از حد مجاز است!"
                            )
                        )
                    ],
                    cache_time=0
                )
                return

            # ایجاد شناسه یکتا برای نجوا
            whisper_id = hashlib.md5(f"{time.time()}{query}".encode()).hexdigest()
            
            # ذخیره نجوا
            self.whispers[whisper_id] = {
                "text": whisper_text,
                "recipient": recipient,
                "sender": inline_query.from_user.id,
                "time": time.time()
            }

            # ایجاد دکمه‌های نجوا
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("👀 مشاهده نجوا", callback_data=f"view_{whisper_id}")
            ]])

            await inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="🤫 نجوای جدید",
                        description=f"برای {recipient}",
                        input_message_content=InputTextMessageContent(
                            f"🤫 یک نجوای محرمانه برای {recipient}\n"
                            "برای مشاهده روی دکمه زیر کلیک کنید."
                        ),
                        reply_markup=keyboard
                    )
                ],
                cache_time=0
            )

        # پردازش کلیک روی دکمه‌ها
        @self.app.on_callback_query()
        async def handle_callback(client, callback: CallbackQuery):
            if not callback.data.startswith("view_"):
                return

            whisper_id = callback.data.split("_")[1]
            
            # بررسی وجود نجوا
            if whisper_id not in self.whispers:
                await callback.answer("❌ این نجوا دیگر در دسترس نیست!", show_alert=True)
                return

            whisper = self.whispers[whisper_id]
            
            # بررسی زمان انقضا
            if time.time() - whisper["time"] > Config.WHISPER_TIMEOUT:
                del self.whispers[whisper_id]
                await callback.answer("❌ این نجوا منقضی شده است!", show_alert=True)
                return

            # بررسی دسترسی کاربر
            user_username = f"@{callback.from_user.username}" if callback.from_user.username else ""
            if (callback.from_user.id != whisper["sender"] and 
                user_username != whisper["recipient"]):
                await callback.answer("❌ این نجوا برای شما نیست!", show_alert=True)
                return

            # نمایش نجوا
            await callback.answer(whisper["text"], show_alert=True)
            
            # حذف نجوا پس از مشاهده
            if callback.from_user.id != whisper["sender"]:
                del self.whispers[whisper_id]
                try:
                    await callback.message.edit_text(
                        "✅ این نجوا خوانده شد و حذف گردید.",
                        reply_markup=None
                    )
                except:
                    pass

    async def start(self):
        """شروع ربات"""
        await self.app.start()
        print("🤖 Whisper Bot is running...")
        await self.app.idle()

    async def stop(self):
        """توقف ربات"""
        await self.app.stop()

# اجرای ربات
if __name__ == "__main__":
    import asyncio
    
    bot = WhisperBot()
    asyncio.get_event_loop().run_until_complete(bot.start())
