import aiomysql
import asyncio
import configparser

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


async def create_connection():
    connection = await aiomysql.connect(host=host, user=user, password=password, db=database,
                                        loop=loop, autocommit=True)
    return connection


async def get_guild_translation(guild_id):
    try:
        connection = await create_connection()
    except:
        return 'haleem'

    async with connection.cursor() as cursor:
        await cursor.execute(f"SELECT translation "
                             f"FROM {server_translations_table_name} "
                             f"WHERE server = {guild_id}")
        result = await cursor.fetchone()
        if result is None:  # If no translation has been set
            connection.close()
            return 'haleem'
        else:
            return result[0]


async def update_guild_translation(guild_id, translation):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        create_sql = f"INSERT INTO {server_translations_table_name} (server, translation) VALUES (%s, %s) " \
                     f"ON DUPLICATE KEY UPDATE server={guild_id}, translation={translation}"
        await cursor.execute(create_sql, (guild_id, translation))
        connection.close()


async def update_server_prayer_times_details(guild_id, channel_id, location, timezone, method):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        create_sql = f"INSERT INTO {server_prayer_times_table_name} (server, channel, location, timezone, calculation_method) " \
                     f"VALUES (%s, %s, %s, %s, %s) "
        await cursor.execute(create_sql, (guild_id, channel_id, location, timezone, method))
        connection.close()


async def delete_server_prayer_times_details(guild_id, channel):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        delete_mysql = f"DELETE FROM {server_prayer_times_table_name} WHERE server = %s AND channel = %s"
        await cursor.execute(delete_mysql, (guild_id, channel))
        connection.close()


async def get_server_prayer_times_details():
    connection = await create_connection()

    async with connection.cursor() as cursor:
        await cursor.execute(f"SELECT * "
                             f"FROM {server_prayer_times_table_name}")

        # This is not ideal since it loads the entire table into memory (PRs for alternatives would be appreciated)
        results = await cursor.fetchall()
        return results


async def update_user_calculation_method(user, method):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        create_sql = f"INSERT INTO {user_prayer_times_table_name} (user, calculation_method) " \
                     "VALUES (%s, %s) " \
                     "ON DUPLICATE KEY UPDATE user=%s, calculation_method=%s"
        await cursor.execute(create_sql, (user, method, user, method))
        connection.close()


async def get_user_calculation_method(user):
    try:
        connection = await create_connection()
    except:
        return 4

    async with connection.cursor() as cursor:
        await cursor.execute(f"SELECT calculation_method "
                             f"FROM {user_prayer_times_table_name} "
                             f"WHERE user = {user}")
        result = await cursor.fetchone()
        if result is None:  # If no calculation method has been set
            connection.close()
            return 4
        else:
            return result[0]
