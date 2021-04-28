import asyncio
import configparser

import aiomysql
import pandas as pd
import pymysql
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


class PrayerTimesHandler(DBHandler):

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
