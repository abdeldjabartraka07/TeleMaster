import logging
import asyncio
import os
import typing

from telethon import events

from telegradd.connect.authorisation.client import TELEGRADD_client
from telegradd.connect.authorisation.databased import Database
from telegradd.adder.adder import ADDER, auth_for_adding
from telegradd.utils import split_ac


async def join_groups_bot(clients: typing.List, group_link: str):
    join_group_tasks = [ADDER(cl).join_group(group_link) for cl in clients]
    res = await asyncio.gather(*join_group_tasks, return_exceptions=True)
    # Filter out successful joins and handle failures
    successful_joins = [r for r in res if not isinstance(r, Exception) and r is not None]
    failed_joins = [r for r in res if isinstance(r, Exception) or r is None]
    return successful_joins, failed_joins


async def main_adder_bot(clients: typing.List, group_link: str, how_to_add: str, users_num: int, message_callback: typing.Callable):
    if how_to_add == 'id':
        await message_callback("WARNING: U can't add via ID a user or interact with a chat through id, that your current session hasn’t met yet. That's why more errors may occur and additional actions would be required!!")
    
    if not clients:
        await message_callback("لا توجد حسابات متاحة للإضافة.")
        return

    await message_callback(f"جاري الانضمام إلى المجموعة {group_link}...")
    successful_joins, failed_joins = await join_groups_bot(clients, group_link)
    if not successful_joins:
        await message_callback(f"فشل الانضمام إلى المجموعة {group_link} بجميع الحسابات. الأخطاء: {failed_joins}")
        return
    else:
        await message_callback(f"تم الانضمام إلى المجموعة {group_link} بنجاح بواسطة {len(successful_joins)} حسابات.")

    client_num = len(successful_joins)
    
    try:
        split_ac(client_num, users_num)
    except TypeError:
        await message_callback('يبدو أنه لا يوجد عدد كافٍ من المستخدمين في ملف users.csv. حاول إضافة المزيد من المستخدمين أو تقليل عدد الحسابات أو المستخدمين.')
        return

    add_user_objects = [ADDER(cl) for cl in successful_joins]
    
    if how_to_add == 'id':
        # Simplified for bot integration, assuming users.csv is pre-populated and no interactive prompts
        await message_callback("جاري الإضافة بواسطة المعرف. تأكد من أن ملف users.csv جاهز.")
        num = 0
        client_tasks = []
        for client in successful_joins:
            client_tasks.append(ADDER(client).add_via_id(f'users{num}.csv', group_link))
            num += 1

        if len(client_tasks) > 5:
            for client_batch in get_batch_acc(batch_size=5, clients=client_tasks):
                await asyncio.gather(*client_batch, return_exceptions=True)
        else:
            await asyncio.gather(*client_tasks, return_exceptions=True)
        await message_callback("تمت محاولة الإضافة بواسطة المعرف.")

    elif how_to_add == 'username':
        await message_callback("جاري الإضافة بواسطة اسم المستخدم. تأكد من أن ملف users.csv جاهز.")
        num = 0
        client_tasks = []
        for client in successful_joins:
            client_tasks.append(ADDER(client).add_via_username(f'users{num}.csv', group_link))
            num += 1
        
        if len(client_tasks) > 5:
            for client_batch in get_batch_acc(batch_size=5, clients=client_tasks):
                await asyncio.gather(*client_batch, return_exceptions=True)
        else:
            await asyncio.gather(*client_tasks, return_exceptions=True)
        await message_callback("تمت محاولة الإضافة بواسطة اسم المستخدم.")

def get_batch_acc(batch_size: int, clients):
    batch = 0
    for _ in range(len(clients) // batch_size + 1):
        if not clients[batch:batch + batch_size]:
            break
        yield clients[batch:batch + batch_size]
        batch += batch_size


async def join_group_bot(group_link: str, message_callback: typing.Callable, account_nums: typing.Optional[typing.List[int]] = None, admin_mode: bool = False):
    await message_callback(f"جاري محاولة الانضمام إلى المجموعة {group_link}...")
    try:
        if account_nums is None or not account_nums:
            clients = await TELEGRADD_client().clients(restriction=False)
        else:
            clients = await TELEGRADD_client(tuple(account_nums)).clients(restriction=False)
        
        if not clients:
            await message_callback("لا توجد حسابات متاحة للانضمام.")
            return False

        successful_joins, failed_joins = await join_groups_bot(clients, group_link)
        if successful_joins:
            await message_callback(f"تم الانضمام إلى المجموعة {group_link} بنجاح بواسطة {len(successful_joins)} حسابات.")
            return True
        else:
            await message_callback(f"فشل الانضمام إلى المجموعة {group_link} بجميع الحسابات. الأخطاء: {failed_joins}")
            return False
    except Exception as e:
        await message_callback(f"حدث خطأ أثناء الانضمام إلى المجموعة: {e}")
        return False


# Placeholder for functions that were removed or modified heavily
def already_skimmed():
    return False # Always return False for bot context

def choose_dialog(dialog_dict: typing.Dict) -> int:
    return list(dialog_dict.values())[0][0] # Return first group ID for simplicity

def get_by_id() -> str:
    return 'y' # Assume 'y' for bot context

def hows_to_add():
    return 60 # Default to 60 users per account for bot context


if __name__ == '__main__':
    asyncio.run(main_adder_bot([], '', 'username', 60, print)) # Example call, not for actual use


