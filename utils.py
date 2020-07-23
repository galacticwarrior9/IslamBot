import aiohttp
import configparser
from bs4 import BeautifulSoup
from discord import Embed
from typing import Union
import discord
import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')


def make_embed(**kwargs):

    """
    Creates an embed message with specified inputs.
    Parameters
    ----------
        author
        author_url
        author_icon
        user
        colour
        fields
        inline
        thumbnail
        image
        footer
        footer_icon
    """

    # Get the attributes from the user
    Empty = Embed.Empty
    if True:
        # Get the author/title information
        author = kwargs.get('author', Empty)
        author_url = kwargs.get('author_url', Empty)
        author_icon = kwargs.get('author_icon', Empty)

        # Get the colour
        colour = kwargs.get('colour', 0)

        # Get the values
        fields = kwargs.get('fields', {})
        inline = kwargs.get('inline', True)
        description = kwargs.get('description', Empty)

        # Footer
        footer = kwargs.get('footer', Empty)
        footer_icon = kwargs.get('footer_icon', Empty)

        # Images
        thumbnail = kwargs.get('thumbnail', False)
        image = kwargs.get('image', False)

    # Filter the colour into a usable form
    if type(colour).__name__ == 'Message':
        colour = colour.author.colour.value
    elif type(colour).__name__ == 'Server':
        colour = colour.me.colour.value
    elif type(colour).__name__ == 'Member':
        colour = colour.colour.value

    # Create an embed object with the specified colour
    embedObj = Embed(colour=colour)

    # Set the normal attributes
    if author != Empty:
        embedObj.set_author(name=author, url=author_url, icon_url=author_icon)
    embedObj.set_footer(text=footer, icon_url=footer_icon)
    embedObj.description = description
    # Set the attributes that have no default
    if image:
        embedObj.set_image(url=image)
    if thumbnail:
        embedObj.set_thumbnail(url=thumbnail)

    # Set the fields
    for i, o in fields.items():
        p = inline
        if type(o) in [tuple, list]:
            p = o[1]
            o = o[0]
        embedObj.add_field(name=i, value=o, inline=p)

    # Return to user
    return embedObj


async def get_site_source(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.read()

    return BeautifulSoup(text.decode('utf-8', 'ignore'), 'html5lib')


def convert_to_arabic_number(number_string):
    dic = {
        '0': '۰',
        '1': '١',
        '2': '٢',
        '3': '۳',
        '4': '٤',
        '5': '٥',
        '6': '٦',
        '7': '٧',
        '8': '٨',
        '9': '۹',
        ':': ':'
    }
    return "".join([dic[char] for char in number_string])


def convert_from_arabic_number(number_string):
    dic = {
     '۹': '9',
     '٨': '8',
     '٧': '7',
     '٦': '6',
     '٥': '5',
     '٤': '4',
     '۳': '3',
     '٢': '2',
     '١': '1',
     '۰': '0',
     ':': ':'
    }
    return "".join([dic[char] for char in number_string])


path = "prefixes.csv"


def make_csv():
    df = pd.DataFrame(columns=['guildID', 'prefix', 'authorID'])
    df.to_csv(path, index=False)


def get_csv():
    try:
        pd.read_csv(path)
    except FileNotFoundError:
        make_csv()

    df = pd.read_csv(path)
    return df


class PrefixHandler:
    df = get_csv()

    @classmethod
    def save(cls):
        cls.df.to_csv(path, index=False)

    @classmethod
    def add_prefix(cls, author: discord.Member, guild_id: int, prefix: str):
        if guild_id not in cls.df.guildID.values:

            new_row = {
                "guildID": guild_id,
                "prefix": prefix,
                "authorID": author.id
            }

            cls.df = cls.df.append(new_row, ignore_index=True)
            cls.save()
        else:
            guild_row = cls.df[cls.df.guildID == guild_id]
            guild_row.prefix.values[0] = prefix
            cls.df[cls.df.guildID == guild_id] = guild_row
            cls.save()

    @classmethod
    def remove_prefix(cls,guild_id : int):
        if guild_id not in cls.df.guildID.values:
            pass
        else:

            cls.df = cls.df[cls.df.guildID != guild_id]
            cls.save()

    @classmethod
    def get_prefix(cls, guild_id: int) -> Union[str, None]:
        prefix = None

        try:
            guild_row = cls.df[cls.df.guildID == guild_id]
            prefix = guild_row.prefix.values[0]
        except:
            pass

        return prefix

    @classmethod
    def get_default_prefix(cls):
        prefix = config['IslamBot']['default_prefix']
        return prefix

    @classmethod
    def has_custom_prefix(cls, guild_id: int) -> bool:

        return guild_id in cls.df.guildID.values
