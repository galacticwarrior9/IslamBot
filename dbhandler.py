import asyncio
import configparser

import aiomysql
import pandas as pd
from aiomysql.sa import create_engine
from sqlalchemy import create_engine

config = configparser.ConfigParser()
config.read('config.ini')

host = config['MySQL']['host']
user = config['MySQL']['user']
password = config['MySQL']['password']
database = config['MySQL']['database']
server_translations_table_name = config['MySQL']['server_translations_table_name']
server_prayer_times_table_name = config['MySQL']['server_prayer_times_table_name']
user_prayer_times_table_name = config['MySQL']['user_prayer_times_table_name']

loop = asyncio.get_event_loop()


class DBHandler:

    host = config['MySQL']['host']
    user = config['MySQL']['user']
    password = config['MySQL']['password']
    database = config['MySQL']['database']
    server_translations_table_name = config['MySQL']['server_translations_table_name']
    server_prayer_times_table_name = config['MySQL']['server_prayer_times_table_name']
    user_prayer_times_table_name = config['MySQL']['user_prayer_times_table_name']

    @classmethod
    async def create_connection(cls):
        connection = await aiomysql.connect(host=host, user=user, password=password, db=database,
                                            loop=loop, autocommit=True)
        return connection

    @classmethod
    async def get_guild_translation(cls, guild_id):
        try:
            connection = await cls.create_connection()
        except:
            return 'haleem'

        async with connection.cursor() as cursor:
            await cursor.execute(f"SELECT translation "
                                 f"FROM {server_translations_table_name} "
                                 f"WHERE server = {guild_id}")
            result = await cursor.fetchone()

            # If no translation has been set, return the default translation:
            if result is None:
                translation = 'haleem'
            else:
                translation = result[0]

            from quran import Translation
            try:
                Translation.get_translation_id(translation)
            except KeyError:
                await cls.delete_guild_translation(guild_id)
                return 'haleem'

            connection.close()
            return translation

    @classmethod
    async def update_guild_translation(cls, guild_id, translation):
        connection = await cls.create_connection()
        async with connection.cursor() as cursor:
            create_sql = f"INSERT INTO {server_translations_table_name} (server, translation) VALUES (%s, %s) " \
                         f"ON DUPLICATE KEY UPDATE server=%s, translation=%s"
            await cursor.execute(create_sql, (guild_id, translation, guild_id, translation))
            connection.close()

    @classmethod
    async def delete_guild_translation(cls, guild_id):
        connection = await cls.create_connection()
        async with connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {server_translations_table_name} WHERE server=%s"
            await cursor.execute(delete_sql, guild_id)
            connection.close()


def create_df():
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:3306/{database}')
    connection = engine.connect()
    user_df = pd.read_sql(f"SELECT * FROM {user_prayer_times_table_name}", connection)
    server_df = pd.read_sql(f"SELECT * FROM {server_prayer_times_table_name}", connection)
    connection.close()
    return user_df, server_df


class PrayerTimesHandler(DBHandler):

    user_df, server_df = create_df()

    @classmethod
    async def update_server_prayer_times_details(cls, guild_id, channel_id, location, timezone, method):
        new_row = {'server': str(guild_id), 'channel': str(channel_id), 'location': location, 'timezone': timezone, 'calculation_method': method}
        if str(channel_id) not in cls.server_df.channel.values:
            cls.server_df = cls.server_df.append(new_row, ignore_index=True)
        else:
            updated_df = pd.DataFrame(new_row, index=[0])
            cls.server_df.update(updated_df)

    @classmethod
    async def delete_server_prayer_times_details(cls, channel):
        if str(channel) not in cls.server_df.channel.values:
            pass
        else:
            cls.server_df = cls.server_df[cls.server_df.channel != str(channel)]

    @classmethod
    async def update_user_prayer_times_details(cls, user_id, location: str, timezone: str, method: str):
        new_row = {'user': str(user_id), 'location': location, 'timezone': timezone, 'calculation_method': method}
        if str(user_id) not in cls.user_df.user.values:
            cls.user_df = cls.user_df.append(new_row, ignore_index=True)
        else:
            updated_df = pd.DataFrame(new_row, index=[0])
            cls.user_df.update(updated_df)

    @classmethod
    async def delete_user_prayer_times_details(cls, user_id):
        if str(user_id) not in cls.user_df.user.values:
            pass
        else:
            cls.user_df = cls.user_df[cls.user_df.user != str(user_id)]

    @classmethod
    async def update_user_calculation_method(cls, user, method):
        connection = await cls.create_connection()
        async with connection.cursor() as cursor:
            create_sql = f"INSERT INTO {user_prayer_times_table_name} (user, calculation_method) " \
                         "VALUES (%s, %s) " \
                         "ON DUPLICATE KEY UPDATE user=%s, calculation_method=%s"
            await cursor.execute(create_sql, (user, method, user, method))
            connection.close()

    @classmethod
    async def get_user_calculation_method(cls, user):
        try:
            connection = await cls.create_connection()
        except:
            return 4

        async with connection.cursor() as cursor:
            await cursor.execute(f"SELECT calculation_method "
                                 f"FROM {user_prayer_times_table_name} "
                                 f"WHERE user = {user}")
            result = await cursor.fetchone()
            if result is None:  # If no calculation method has been set
                method = 4
            else:
                method = result[0]
            connection.close()
            return method
