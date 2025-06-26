
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", ",").split(",") if x]

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("Please set API_ID, API_HASH, and BOT_TOKEN environment variables.")
    exit(1)

client = TelegramClient("bot", int(API_ID), API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    await event.reply("مرحباً بك في بوت Telegradd!\nاستخدم /help لعرض الأوامر المتاحة.")

@client.on(events.NewMessage(pattern="/help"))
async def help_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    help_text = (
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه الرسالة\n"
        "/add_session <session_string> - إضافة جلسة Telethon\n"
        "/list_accounts - عرض الحسابات الموجودة\n"
        "/delete_banned - حذف الحسابات المحظورة\n"
        "/join_group <group_link> - الانضمام إلى مجموعة\n"
        "/add_by_id <session_id> <user_id> <group_link> - إضافة عضو بالمعرف\n"
        "/add_by_username <session_id> <username> <group_link> - إضافة عضو باسم المستخدم\n"
        "/parse_group <session_id> <group_link> <type> - سحب أعضاء مجموعة (الأنواع: participants, hidden, comments)\n"
        "/test_auth <session_id> - اختبار صلاحية الجلسة\n"
        "/update_credentials <session_id> <option> <value> - تحديث بيانات الجلسة\n"
        "/delete_duplicates - حذف الجلسات المكررة\n"
        "/delete_accounts <session_id(s) or all> - حذف جميع الحسابات\n"
    )
    await event.reply(help_text)


# Import functions from the original Telegradd script (modified for bot use)
from telegradd.adder.main_adder import main_adder_bot, join_group_bot
from telegradd.connect.authorisation.main_auth import add_account_bot, view_account_bot, delete_banned_bot, auth_for_test_bot, \
    update_credentials_bot, delete_duplicates_csv_bot, delete_accounts_bot
from telegradd.parser.main_parser import parser_page_bot
from telegradd.connect.authorisation.client import TELEGRADD_client


@client.on(events.NewMessage(pattern="/add_session (.*)"))
async def add_session_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    session_string = event.pattern_match.group(1).strip()
    if not session_string:
        await event.reply("الرجاء تزويد سلسلة الجلسة.")
        return
    
    await add_account_bot(session_string, event.reply)

@client.on(events.NewMessage(pattern="/list_accounts"))
async def list_accounts_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    try:
        accounts = view_account_bot()
        if not accounts:
            await event.reply("لا توجد حسابات محفوظة.")
            return
        accounts_list = "الحسابات المحفوظة:\n"
        for acc in accounts:
            accounts_list += f"- ID: {acc[0]}, Name: {acc[1]}\n"
        await event.reply(accounts_list)
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء عرض الحسابات: {e}")

@client.on(events.NewMessage(pattern="/delete_banned"))
async def delete_banned_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    try:
        moved_count = delete_banned_bot()
        await event.reply(f"تم حذف {moved_count} حسابات محظورة.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف الحسابات المحظورة: {e}")

@client.on(events.NewMessage(pattern="/join_group (.*)"))
async def join_group_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    group_link = event.pattern_match.group(1).strip()
    if not group_link:
        await event.reply("الرجاء تزويد رابط المجموعة.")
        return
    
    await join_group_bot(group_link, event.reply)

@client.on(events.NewMessage(pattern="/add_by_id (.*) (.*) (.*)"))
async def add_by_id_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    args = event.pattern_match.groups()
    session_id_str = args[0].strip()
    user_id = args[1].strip()
    group_link = args[2].strip()

    if not all([session_id_str, user_id, group_link]):
        await event.reply("الرجاء تزويد معرف الجلسة، معرف المستخدم، ورابط المجموعة.")
        return
    try:
        session_id = int(session_id_str)
        clients = await TELEGRADD_client((session_id,)).clients(restriction=False)
        if not clients:
            await event.reply(f"لم يتم العثور على الجلسة بالمعرف {session_id_str} أو أنها غير صالحة.")
            return
        
        await event.reply(f"جاري إضافة المستخدم {user_id} إلى المجموعة {group_link} باستخدام الجلسة {session_id_str}...")
        # For simplicity, assuming users.csv is pre-populated and users_num is fixed
        await main_adder_bot(clients, group_link, 'id', 60, event.reply)
        await event.reply("تمت محاولة الإضافة بواسطة المعرف.")
    except ValueError:
        await event.reply("معرف الجلسة يجب أن يكون رقمًا صحيحًا.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الإضافة بالمعرف: {e}")

@client.on(events.NewMessage(pattern="/add_by_username (.*) (.*) (.*)"))
async def add_by_username_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    args = event.pattern_match.groups()
    session_id_str = args[0].strip()
    username = args[1].strip()
    group_link = args[2].strip()

    if not all([session_id_str, username, group_link]):
        await event.reply("الرجاء تزويد معرف الجلسة، اسم المستخدم، ورابط المجموعة.")
        return
    try:
        session_id = int(session_id_str)
        clients = await TELEGRADD_client((session_id,)).clients(restriction=False)
        if not clients:
            await event.reply(f"لم يتم العثور على الجلسة بالمعرف {session_id_str} أو أنها غير صالحة.")
            return

        await event.reply(f"جاري إضافة المستخدم {username} إلى المجموعة {group_link} باستخدام الجلسة {session_id_str}...")
        # For simplicity, assuming users.csv is pre-populated and users_num is fixed
        await main_adder_bot(clients, group_link, 'username', 60, event.reply)
        await event.reply("تمت محاولة الإضافة باسم المستخدم.")
    except ValueError:
        await event.reply("معرف الجلسة يجب أن يكون رقمًا صحيحًا.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء الإضافة باسم المستخدم: {e}")

@client.on(events.NewMessage(pattern="/parse_group (.*) (.*) (.*)"))
async def parse_group_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    args = event.pattern_match.groups()
    session_id_str = args[0].strip()
    group_link = args[1].strip()
    parse_type = args[2].strip().lower()

    if not all([session_id_str, group_link, parse_type]):
        await event.reply("الرجاء تزويد معرف الجلسة، رابط المجموعة، ونوع السحب (participants, hidden, comments).")
        return
    
    if parse_type not in ["participants", "hidden", "comments"]:
        await event.reply("نوع السحب غير صالح. الأنواع المدعومة هي: participants, hidden, comments.")
        return

    try:
        session_id = int(session_id_str)
        clients = await TELEGRADD_client((session_id,)).clients(restriction=False)
        if not clients:
            await event.reply(f"لم يتم العثور على الجلسة بالمعرف {session_id_str} أو أنها غير صالحة.")
            return
        
        # Get the client object from the list (assuming only one client is returned for a single session_id)
        telethon_client = clients[0]

        await event.reply(f"جاري سحب أعضاء المجموعة {group_link} من نوع {parse_type} باستخدام الجلسة {session_id_str}...")
        
        # Map parse_type to us_option for parser_page_bot
        us_option_map = {
            "participants": 6,
            "hidden": 7,
            "comments": 8
        }
        us_option = us_option_map.get(parse_type)

        # Get entity for the group link
        try:
            entity = await telethon_client.get_entity(group_link)
        except Exception as e:
            await event.reply(f"فشل الحصول على معلومات المجموعة: {e}")
            return

        await parser_page_bot(telethon_client, entity, event.reply, us_option=us_option)
        await event.reply(f"تمت عملية سحب الأعضاء من نوع {parse_type}.")

    except ValueError:
        await event.reply("معرف الجلسة يجب أن يكون رقمًا صحيحًا.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء سحب أعضاء المجموعة: {e}")

@client.on(events.NewMessage(pattern="/test_auth (.*)"))
async def test_auth_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    session_id_str = event.pattern_match.group(1).strip()
    if not session_id_str:
        await event.reply("الرجاء تزويد معرف الجلسة.")
        return
    try:
        session_id = int(session_id_str)
        await event.reply(f"جاري اختبار صلاحية الجلسة {session_id_str}...")
        success, message = await auth_for_test_bot(account_nums=[session_id])
        if success:
            await event.reply(f"الجلسة {session_id_str} صالحة.")
        else:
            await event.reply(f"الجلسة {session_id_str} غير صالحة أو حدث خطأ: {message}")
    except ValueError:
        await event.reply("معرف الجلسة يجب أن يكون رقمًا صحيحًا.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء اختبار الصلاحية: {e}")

@client.on(events.NewMessage(pattern="/update_credentials (.*) (.*) (.*)"))
async def update_credentials_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    args = event.pattern_match.groups()
    session_id_str = args[0].strip()
    option_str = args[1].strip()
    value = args[2].strip()

    if not all([session_id_str, option_str, value]):
        await event.reply("الرجاء تزويد معرف الجلسة، الخيار، والقيمة الجديدة.")
        return
    try:
        session_id = int(session_id_str)
        option = int(option_str)
        if not (1 <= option <= 7):
            await event.reply("الخيار يجب أن يكون رقمًا بين 1 و 7.")
            return

        await event.reply(f"جاري تحديث بيانات الجلسة {session_id_str}...")
        success = update_credentials_bot(session_id, option, value)
        if success:
            await event.reply(f"تم تحديث بيانات الجلسة {session_id_str} بنجاح.")
        else:
            await event.reply(f"فشل تحديث بيانات الجلسة {session_id_str}.")
    except ValueError:
        await event.reply("معرف الجلسة والخيار يجب أن يكونا أرقامًا صحيحة.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء تحديث البيانات: {e}")

@client.on(events.NewMessage(pattern="/delete_duplicates"))
async def delete_duplicates_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    try:
        deleted_count = delete_duplicates_csv_bot()
        await event.reply(f"تم حذف {deleted_count} إدخالات مكررة من ملف المستخدمين.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف الجلسات المكررة: {e}")

@client.on(events.NewMessage(pattern="/delete_accounts"))
async def delete_accounts_command(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.reply("غير مصرح لك باستخدام هذا البوت.")
        return
    try:
        # Allow deleting specific accounts by ID or all accounts
        # Example: /delete_accounts 1 2 3 or /delete_accounts all
        args = event.pattern_match.group(1).strip()
        account_ids_to_delete = []
        if args.lower() == 'all':
            account_ids_to_delete = ['all']
        else:
            try:
                account_ids_to_delete = [int(x) for x in args.split()]
            except ValueError:
                await event.reply("الرجاء تزويد معرفات حسابات صحيحة مفصولة بمسافات أو كلمة 'all'.")
                return

        deleted_count = delete_accounts_bot(account_ids_to_delete)
        await event.reply(f"تم حذف {deleted_count} حسابات.")
    except Exception as e:
        await event.reply(f"حدث خطأ أثناء حذف جميع الحسابات: {e}")


async def main():
    print("Bot started. Listening for commands...")
    if not os.path.exists("sessions"): # This is for the bot's own session, not Telegradd's
        os.makedirs("sessions")
    # Ensure Telegradd's session directories exist
    telegradd_sessions_path = os.path.join(os.path.dirname(__file__), 'telegradd', 'sessions', 'session_store')
    telegradd_banned_path = os.path.join(os.path.dirname(__file__), 'telegradd', 'sessions', 'banned')
    os.makedirs(telegradd_sessions_path, exist_ok=True)
    os.makedirs(telegradd_banned_path, exist_ok=True)

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())



