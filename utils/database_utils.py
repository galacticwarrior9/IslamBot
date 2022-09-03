import asyncio
import configparser

import aiomysql

config = configparser.ConfigParser()
config.read('config.ini')

host = config['MySQL']['host']
user = config['MySQL']['user']
password = config['MySQL']['password']
database = config['MySQL']['database']

loop = asyncio.get_event_loop()


class DBHandler:
    def __init__(self, table_name: str, column1: str, column2: str, default_value):
        self.table_name = table_name
        self.column1 = column1  # e.g in the prayer times table, user is column1
        self.column2 = column2  # and calculation_method is column2
        self.default_value = default_value  # would be 4 in the prayer times table

    @classmethod
    async def create_connection(cls):
        connection = await aiomysql.connect(host=host, user=user, password=password, db=database,
                                            loop=loop, autocommit=True)
        return connection

    async def _get_data(self, key):
        try:
            connection = await self.create_connection()
        except:
            return self.default_value

        async with connection.cursor() as cursor:
            await cursor.execute(f"SELECT {self.column2} "
                                 f"FROM {self.table_name} "
                                 f"WHERE {self.column1} = {key}")
            result = await cursor.fetchone()
            connection.close()

            if result is None:
                return self.default_value

            return result[0]

    async def _update_data(self, key, value):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            create_sql = f"INSERT INTO {self.table_name} ({self.column1}, {self.column2}) " \
                         "VALUES (%s, %s) " \
                         f"ON DUPLICATE KEY UPDATE {self.column1}=%s, {self.column2}=%s"
            await cursor.execute(create_sql, (key, value, key, value))
            connection.close()

    async def _delete_data(self, key):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {self.table_name} WHERE {self.column1}=%s"
            await cursor.execute(delete_sql, key)
            connection.close()


class ServerTranslation(DBHandler):
    def __init__(self):
        super().__init__(
            table_name=config['MySQL']['server_translations_table_name'],
            column1='server',
            column2='translation',
            default_value='haleem'
        )

    async def get(self, guild_id) -> str:
        return await self._get_data(guild_id)

    async def update(self, guild_id, translation):
        return await self._update_data(guild_id, translation)

    async def delete(self, guild_id):
        return await self._delete_data(guild_id)


class ServerTafsir(DBHandler):
    def __init__(self):
        super().__init__(
            table_name=config['MySQL']['server_tafsir_table_name'],
            column1='server',
            column2='tafsir',
            default_value='maarifulquran'
        )

    async def get(self, guild_id) -> str:
        return await self._get_data(guild_id)

    async def update(self, guild_id, tafsir):
        return await self._update_data(guild_id, tafsir)

    async def delete(self, guild_id):
        return await self._delete_data(guild_id)


class ServerArabicTafsir(DBHandler):
    def __init__(self):
        super().__init__(
            table_name=config['MySQL']['server_atafsir_table_name'],
            column1='server',
            column2='atafsir',
            default_value='tabari'
        )

    async def get(self, guild_id) -> str:
        return await self._get_data(guild_id)

    async def update(self, guild_id, atafsir):
        return await self._update_data(guild_id, atafsir)

    async def delete(self, guild_id):
        return await self._delete_data(guild_id)


class UserPrayerCalculationMethod(DBHandler):
    def __init__(self):
        super().__init__(
            table_name=config['MySQL']['user_prayer_times_table_name'],
            column1='user',
            column2='calculation_method',
            default_value=4
        )

    async def get(self, user_id) -> int:
        return int(await self._get_data(user_id))

    async def update(self, user_id, calculation_method):
        return await self._update_data(user_id, calculation_method)

    async def delete(self, user_id):
        return await self._delete_data(user_id)