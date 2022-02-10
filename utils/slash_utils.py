from discord_slash.utils.manage_commands import create_choice

MAX_CHOICES = 25


def generate_choices_from_dict(dictionary: dict):
    choices = []
    for key in list(dictionary.keys())[0:MAX_CHOICES - 1]:
        choices.append(create_choice(name=dictionary[key], value=key))
    return choices


def generate_choices_from_list(lst: list):
    choices = []
    for entry in lst[0:MAX_CHOICES - 1]:
        choices.append(create_choice(name=entry, value=entry))
    return choices
