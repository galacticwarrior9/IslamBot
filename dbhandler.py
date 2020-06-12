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
        await cursor.execute(f"SELECT translation FROM {server_translations_table_name}"
                             f" WHERE server = {guild_id}")
        result = await cursor.fetchone()
        try:
            result = result[0]
            connection.close()
        except TypeError:
            connection.close()
            return 'haleem'
        return result


async def update_guild_translation(guild_id, translation):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        create_sql = f"INSERT IGNORE INTO {server_translations_table_name} (server, translation) VALUES (%s, %s)"
        update_sql = f"UPDATE {server_translations_table_name} SET translation = %s WHERE server = %s"
        await cursor.execute(create_sql, (guild_id, translation))
        await cursor.execute(update_sql, (translation, guild_id))
        connection.close()

