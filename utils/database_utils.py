import asyncio
import os

import aiomysql

host = os.environ.get('MYSQL_HOST', 'db')
user = os.environ.get('MYSQL_USER', 'islambot_user')
password = os.environ.get('MYSQL_PASSWORD', 'islambot_password')
database = os.environ.get('MYSQL_DATABASE', 'islambot')

SERVER_TRANSLATIONS_TABLE = os.environ.get('MYSQL_SERVER_TRANSLATIONS_TABLE', 'server_translations')
SERVER_TAFSIR_TABLE = os.environ.get('MYSQL_SERVER_TAFSIR_TABLE', 'server_tafsir')
SERVER_ATAFSIR_TABLE = os.environ.get('MYSQL_SERVER_ATAFSIR_TABLE', 'server_atafsir')
USER_PRAYER_TIMES_TABLE = os.environ.get('MYSQL_USER_PRAYER_TIMES_TABLE', 'user_prayer')

loop = asyncio.get_event_loop()


class DBHandler:
    def __init__(self, table_name: str, column1: str, column2: str, default_value, key):
        self.table_name = table_name
        self.column1 = column1  # e.g in the prayer times table, user is column1
        self.column2 = column2  # and calculation_method is column2
        self.default_value = default_value  # would be 4 in the prayer times table
        self.key = key

    @classmethod
    async def create_connection(cls):
        connection = await aiomysql.connect(host=host, user=user, password=password, db=database,
                                            loop=loop, autocommit=True)
        return connection

    async def _get_data(self):
        try:
            connection = await self.create_connection()
        except:
            return self.default_value

        try:
            async with connection.cursor() as cursor:
                await cursor.execute(f"SELECT {self.column2} "
                                     f"FROM {self.table_name} "
                                     f"WHERE {self.column1} = {self.key}")
                result = await cursor.fetchone()
                connection.close()

                if result is None:
                    return self.default_value

                return result[0]
        except:
            connection.close()
            return self.default_value

    async def _update_data(self, value):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            create_sql = f"INSERT INTO {self.table_name} ({self.column1}, {self.column2}) " \
                         "VALUES (%s, %s) " \
                         f"ON DUPLICATE KEY UPDATE {self.column1}=%s, {self.column2}=%s"
            await cursor.execute(create_sql, (self.key, value, self.key, value))
            connection.close()

    async def _delete_data(self):
        connection = await self.create_connection()
        async with connection.cursor() as cursor:
            delete_sql = f"DELETE FROM {self.table_name} WHERE {self.column1}=%s"
            await cursor.execute(delete_sql, self.key)
            connection.close()


class ServerTranslation(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=SERVER_TRANSLATIONS_TABLE,
            column1='server',
            column2='translation',
            default_value='haleem',
            key=guild_id
        )

    async def get(self) -> str:
        return await self._get_data()

    async def update(self, translation):
        return await self._update_data(translation)

    async def delete(self):
        return await self._delete_data()


class ServerTafsir(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=SERVER_TAFSIR_TABLE,
            column1='server',
            column2='tafsir',
            default_value='maarifulquran',
            key=guild_id,
        )

    async def get(self) -> str:
        return await self._get_data()

    async def update(self, tafsir):
        return await self._update_data(tafsir)

    async def delete(self):
        return await self._delete_data()


class ServerArabicTafsir(DBHandler):
    def __init__(self, guild_id: int):
        super().__init__(
            table_name=SERVER_ATAFSIR_TABLE,
            column1='server',
            column2='atafsir',
            default_value='tabari',
            key=guild_id,
        )

    async def get(self) -> str:
        return await self._get_data()

    async def update(self, atafsir):
        return await self._update_data(atafsir)

    async def delete(self):
        return await self._delete_data()


class UserPrayerCalculationMethod(DBHandler):
    def __init__(self, user_id):
        super().__init__(
            table_name=USER_PRAYER_TIMES_TABLE,
            column1='user_id',
            column2='calculation_method_id',
            default_value=4,
            key=user_id,
        )

    async def get(self) -> int:
        return int(await self._get_data())

    async def update(self, calculation_method):
        return await self._update_data(calculation_method)

    async def delete(self):
        return await self._delete_data()
