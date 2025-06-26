import asyncio
import os.path
from typing import Any
import logging
from telethon import TelegramClient
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin, ChannelParticipantsRecent, \
    UserStatusOffline, \
    UserStatusLastWeek, UserStatusLastMonth, UserStatusOnline, UserStatusRecently
from telethon.tl.functions.users import GetFullUserRequest
import pathlib
import aiofiles

from telegradd.connect.authorisation.client import TELEGRADD_client
from telegradd.connect.authorisation.databased import Database
from telegradd.parser.filters import Filter


class PARSER:
    LAST_MONTH = UserStatusLastMonth
    LAST_WEEK = UserStatusLastWeek
    OFFLINE = UserStatusOffline
    ONLINE = UserStatusOnline
    RECENTLY = UserStatusRecently

    def __init__(self, client: TelegramClient, status: Any = False, username=False, black_list_name: bool = False,
                 black_list_bio: bool = False,
                 photo: bool = False, premium: bool = False, phone: bool = False, without_username=False):
        self.without_username = without_username
        self.phone = phone
        self.premium = premium
        self.photo = photo
        self.black_list_bio = black_list_bio
        self.black_list_name = black_list_name
        self.status = status
        self.client = client
        self.username = username
        self._filename = pathlib.Path (pathlib.Path (__file__).parents[1], 'users', 'users.csv')
        os.makedirs(self._filename.parent, exist_ok=True)

    async def write_users(self, user, title):
        if not self._filename.exists (): # Check if file exists before writing header
            async with aiofiles.open (self._filename, 'a', encoding='UTF-8') as f:
                await f.write (f'user_id:first_name:username:access_hash:phone:group')
                await f.write (f'\n{user.id}:{user.first_name}:{user.username}:{user.access_hash}:{user.phone}:{title}')
        else:
            async with aiofiles.open (self._filename, 'a', encoding='UTF-8') as f:
                await f.write (f'\n{user.id}:{user.first_name}:{user.username}:{user.access_hash}:{user.phone}:{title}')

    # Removed interactive get_dialogs and get_channels as they are not suitable for bot

    def filter(self, user, participant=True, bio=None):
        us_filter = Filter (user)
        if (participant and isinstance (user.participant, ChannelParticipantCreator)) or (participant and
            isinstance (user.participant, ChannelParticipantAdmin) ):
                return False
        elif us_filter.standard_filter:
            return False
        elif self.status and (us_filter.status (self.status) is False):
            return False
        elif self.phone and us_filter.phone is False:
            return False
        elif self.photo and us_filter.photo is False:
            return False
        elif self.premium and us_filter.premium:  # dont include premium users
            return False
        elif self.black_list_bio:
            if us_filter.bio(bio):
                return False
        elif self.black_list_name and us_filter.name:
            return False
        elif self.username and (us_filter.username is False):
            return False
        elif self.without_username and (us_filter.without_username is False):
            return False
        return True

    async def participants_scraper(self, entity, limit=None, status_filter=ChannelParticipantsRecent (), bio=False):
        async with self.client:
            title = entity.title if hasattr(entity, 'title') else str(entity.id)
            async for user in self.client.iter_participants (entity, limit=limit, filter=status_filter):
                try:
                    if bio:
                        full = await self.client (GetFullUserRequest (user))
                        bio_text = full.full_user.about
                        if self.filter (user, bio=bio_text):
                            await self.write_users(user, title)
                    else:
                        if self.filter (user):
                            await self.write_users(user, title)
                except Exception as err:
                    logging.error(f"Error processing user in participants_scraper: {err}")
                    continue
        logging.info('Successfully parsed participants')

    async def from_message_scraper(self, entity, limit=None, bio=False):
        async with self.client:
            replies = []
            lap = 0
            title = entity.title if hasattr(entity, 'title') else str(entity.id)
            async for mes in self.client.iter_messages (entity, limit=limit):
                lap += 1
                try:
                    if mes.from_id:
                        user = await self.client.get_entity(mes.from_id)
                        if user.id not in replies:
                            replies.append(user.id)
                        else:
                            continue
                        try:
                            if bio:
                                full = await self.client (GetFullUserRequest (user))
                                bio_text = full.full_user.about
                                if self.filter (user, bio=bio_text, participant=False):
                                    await self.write_users (user, title)
                            else:
                                if self.filter (user, participant=False):
                                    await self.write_users (user, title)
                        except Exception as err:
                            logging.error(f"Error processing user in from_message_scraper: {err}")
                            continue
                except Exception as err:
                    logging.error(f"Error processing message in from_message_scraper: {err}")
                    continue
        logging.info('Successfully parsed from messages')

    async def from_comments(self, entity, limit=None, bio=False):
        async with self.client:
            title = entity.title if hasattr(entity, 'title') else str(entity.id)
            async for mes in self.client.iter_messages (entity, limit=limit):
                replies = []
                if (mes.replies is not None) and (mes.replies.comments):
                    async for reply in self.client.iter_messages (entity, reply_to=mes.id):
                        try:
                            if reply.from_id:
                                user = await self.client.get_entity (reply.from_id)
                                if user.id not in replies:
                                    replies.append (user.id)
                                else:
                                    continue
                                try:
                                    if bio:
                                        full = await self.client (GetFullUserRequest (user))
                                        bio_text = full.full_user.about
                                        if self.filter (user, participant=False, bio=bio_text):
                                            await self.write_users (user, title)
                                    else:
                                        if self.filter (user, participant=False):
                                            await self.write_users (user, title)
                                except Exception as err:
                                    logging.error(f"Error processing user in from_comments: {err}")
                                    continue
                        except Exception as err:
                            logging.error(f"Error processing reply in from_comments: {err}")
                            continue
        logging.info('Successfully parsed from comments')


# Removed interactive auth_for_parsing and main functions

if __name__ == '__main__':
    # Example usage for testing, not for bot operation
    pass


