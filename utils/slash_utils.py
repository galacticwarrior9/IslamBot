from discord.app_commands import Choice

MAX_CHOICES = 25


def generate_choices_from_dict(dictionary: dict):
    choices = []
    for key in list(dictionary.keys())[0:MAX_CHOICES - 1]:
        choices.append(Choice(name=dictionary[key], value=key))
    return choices


def generate_choices_from_list(lst: list):
    choices = []
    for entry in lst[0:MAX_CHOICES - 1]:
        choices.append(Choice(name=entry, value=entry))
    return choices


def get_key_from_value(value, dict: dict):
    for dict_key, dict_value in dict.items():
        if value == dict_value:
            print(value)
            return dict_key
    return None
