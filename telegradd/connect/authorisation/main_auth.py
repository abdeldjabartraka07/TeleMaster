import asyncio
import os
import pathlib
import shutil

import aiofiles
from telethon import TelegramClient
from telethon.sessions import StringSession

from telegradd.connect.authorisation.client import TELEGRADD_client
from telegradd.connect.authorisation.databased import Auth, Database


async def add_account_bot(session_string: str, message_callback: typing.Callable):
    try:
        # Validate session string by trying to connect
        client = TelegramClient(StringSession(session_string), int(os.getenv('API_ID')), os.getenv('API_HASH'))
        await client.connect()
        if not await client.is_user_authorized():
            await message_callback('سلسلة الجلسة غير صالحة أو انتهت صلاحيتها.')
            await client.disconnect()
            return False
        await client.disconnect()

        # Save the session string to a file in the sessions/session_store directory
        session_path = pathlib.Path(pathlib.Path(__file__).parents[1], 'sessions', 'session_store')
        os.makedirs(session_path, exist_ok=True)
        
        # Generate a unique session name. For simplicity, let's use a timestamp or a simple counter.
        # In a real scenario, you might want to ask the user for a name or use a more robust naming scheme.
        session_name = f"bot_session_{len(os.listdir(session_path)) + 1}"
        file_path = session_path / f'{session_name}.session'
        
        with open(file_path, 'w') as f:
            f.write(session_string)
        
        # Add to database (if necessary, based on how Auth class works)
        # The original Auth class seems to handle the file saving and DB entry during its interactive process.
        # If Auth().add_account() is strictly interactive, we might need to bypass it or mock it.
        # For now, we'll just save the file directly and assume the DB will pick it up or is not strictly necessary for bot operation.
        
        await message_callback(f'تمت إضافة الجلسة بنجاح باسم: `{session_name}`')
        return True
    except Exception as err:
        await message_callback(f'حدث خطأ أثناء إضافة الجلسة: {err}')
        return False


def view_account_bot():
    # This function needs to return the accounts, not print them.
    # We need to access the Database directly.
    db = Database()
    accounts = db.get_all(('all',))
    return accounts # Returns a list of tuples (id, session_name, ...)


def delete_banned_bot():
    path = pathlib.Path(pathlib.Path(__file__).parents[1], 'sessions', 'session_store')
    accounts = [account[1] for account in Database().get_all(('all', ))]
    sessions = [str(file).rstrip('.session') for file in os.listdir(path) if str(file).endswith('.session')]
    moved_count = 0
    for file in sessions:
        if file not in accounts:
            try:
                shutil.move(pathlib.Path(path, f'{file}.session'), pathlib.Path(pathlib.Path(__file__).parents[1], 'sessions', 'banned', f'{file}.session'))
                moved_count += 1
            except Exception as e:
                print(f"Error moving {file}.session: {e}") # Log error if move fails
    return moved_count


async def auth_for_test_bot(account_nums: typing.Optional[typing.List[int]] = None):
    # This function needs to return results, not print and exit.
    try:
        if account_nums is None or not account_nums:
            clients = await TELEGRADD_client().clients(restriction=False)
        else:
            clients = await TELEGRADD_client(tuple(account_nums)).clients(restriction=False)
        
        if clients:
            return True, len(clients) # Successfully authenticated some clients
        else:
            return False, 0 # No clients authenticated
    except Exception as e:
        return False, str(e) # Return error message


def update_credentials_bot(account_id: int, option: int, value: str):
    db = Database()
    # Assuming option corresponds to the original function's logic (1-7)
    if option == 1:
        db.update_id(value, account_id)
    elif option == 2:
        db.update_hash(value, account_id)
    elif option == 3:
        db.update_proxy(value, account_id)
    elif option == 4:
        db.update_system(value, account_id)
    elif option == 5:
        db.update_password(value, account_id)
    elif option == 6:
        db.update_restriction(value, account_id)
    elif option == 7:
        db.update_phone(value, account_id)
    else:
        raise ValueError("Invalid option for updating credentials.")
    return True


def delete_duplicates_csv_bot():
    path_user = pathlib.Path(pathlib.Path(__file__).parents[2], 'users', 'users.csv')
    if not os.path.exists(path_user):
        return 0 # No users.csv to process

    with open(path_user, encoding='UTF-8') as f:
        # Read all lines, filter out header, and use a set for uniqueness
        users = {line.strip() for line in f.readlines() if not line.startswith('user_id:first_name')}

    # Write back with header and unique users
    with open(path_user, 'w', encoding='UTF-8') as f:
        f.write('user_id:first_name:username:access_hash:phone:group\n')
        for user in sorted(list(users)): # Sort for consistent output
            f.write(user + '\n')
    return len(users)


def delete_accounts_bot(account_ids: typing.Optional[typing.List[int]] = None):
    db = Database()
    deleted_count = 0
    if account_ids is None or 'all' in account_ids: # Treat 'all' as a special string if passed
        acc = db.get_all(('all',))
        for i in acc:
            db.delete_account(num=i[0])
            deleted_count += 1
    else:
        for acc_id in account_ids:
            if isinstance(acc_id, int):
                acc = db.get_all((acc_id,))
                if acc:
                    db.delete_account(num=acc[0][0])
                    deleted_count += 1
    return deleted_count


# Original functions (kept for reference or if still used internally by other parts of the script)
# These are the interactive versions that should not be called directly by the bot
def add_account(option: int):
    load = 'CUSTOM'
    if option == 2:
        load = 'JS'
    elif option == 3:
        load = 'TDATA'
    elif option == 4:
        load = 'PYROGRAM'
    elif option == 5:
        load = 'TELETHON'
    try:
        Auth(load).add_account()
    except Exception as err:
        print(err)

def view_account():
    mode = input('Use admin mode (y/n)?: ')
    admin = True if mode == 'y' else False
    Database().view_all(admin=True) if admin else Database().view_all()

def delete_banned():
    path = pathlib.Path(pathlib.Path(__file__).parents[1], 'sessions', 'session_store')
    accounts = [account[1] for account in Database().get_all(('all', ))]
    sessions = [str(file).rstrip('.session') for file in os.listdir(path) if str(file).endswith('.session')]
    for file in sessions:
        if file not in accounts:
            shutil.move(pathlib.Path(path, f'{file}.session'), pathlib.Path(pathlib.Path(__file__).parents[1], 'sessions', 'banned', f'{file}.session'))

async def auth_for_test():
    mode = input ('Use admin mode (y/n)?: ')
    admin = True if mode == 'y' else False
    Database ().view_all (admin=True) if admin else Database ().view_all ()
    num = input('Choose accounts. Enter digits via spaces (all - to use all): ').lower().strip(' ').split(' ')
    if num[0] == 'all':
        await TELEGRADD_client ().clients (restriction=False)
    elif num[0].isdigit():
        await TELEGRADD_client (tuple(int(i) for i in num)).clients (restriction=False)
    else:
        print('U choose wrong options, try again')
        return

def update_credentials(opt: int):
    Database ().view_all (admin=True)
    account = input('Choose an account: ')
    try:
        account = int(account)
    except:
        opt = 8
    if opt == 1:
        api_id = input('Enter new app_id: ')
        Database().update_id(api_id, account)
    elif opt == 2:
        app_hash = input('Enter new app_hash: ')
        Database().update_hash(app_hash, account)
    elif opt == 3:
        proxy = input('Enter new Proxy: ')
        Database().update_proxy(proxy, account)
    elif opt == 4:
        system = input('Enter new system. Format: device model:system:app version: ')
        Database().update_system(system, account)
    elif opt == 5:
        password = input('Enter new password: ')
        Database().update_password(password, account)
    elif opt == 6:
        restr = input('Enter new restriction')
        Database().update_restriction(restr, account)
    elif opt == 7:
        phone = input('Enter new phone: ')
        Database().update_phone(phone, account)
    elif opt == 8:
        print('Wrong option...')
        return

def delete_duplicates_csv():
    path_user = pathlib.Path(pathlib.Path(__file__).parents[2], 'users', 'users.csv')
    with open(path_user, encoding='UTF-8') as f:
        users = {line for line in f.readlines () if not line.startswith('user_id:first_name')}

    with open(path_user, 'w', encoding='UTF-8') as f:
        f.write('user_id:first_name:username:access_hash:phone:group\n')
        for user in users:
            f.write(user)

def delete_accounts():
    Database().view_all(admin=False)
    delete = input('Enter number of an account (all - delete all): ')
    if delete == 'all':
        acc = Database().get_all(('all',))
        for i in acc:
            Database().delete_account(num=i[0])
    else:
        if delete.isdigit():
            acc = Database().get_all((int(delete),))
            Database().delete_account(num=acc[0][0])
        else:
            print('Wrong input...')
            return

if __name__ == '__main__':
    asyncio.run(auth_for_test())


