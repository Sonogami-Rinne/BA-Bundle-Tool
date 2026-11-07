import json
import os.path

base_path = r'E:\@\extracted\jp\windows\extracted\tables\semantic\ExcelDB'
base_voice_path = r'E:\@\extracted\jp\windows\extracted\media'
base_bgm_path = (r'E:\@\extracted\jp\windows\raw\media\GameData\Audio\BGM', r'E:\@\extracted\jp\windows\raw\media\Prologue\Audio\BGM')

db_character = {}
db_memory_lobby = {}
db_character_dialog = {}
db_voice_spine = {}
db_voice = {}
db_bgm = {}

with open(os.path.join(base_path, 'CharacterDBSchema.json'), 'r', encoding='utf-8') as f:
    for cha in json.load(f):
        info = cha['Bytes']
        db_character[info['Id']] = {
            'id': info['Id'],
            'devName': info['DevName'],
            'school': info['School'],
            'club': info['Club'],
            'resourceName': info['ScenarioCharacter']
        }

with open(os.path.join(base_path, 'MemoryLobbyDBSchema.json'), 'r', encoding='utf-8') as f:
    for lob in json.load(f):
        info = lob['Bytes']
        db_memory_lobby[info['PrefabName'].lower()] = {
            'character': info['CharacterId'],
            'bgm': info['BGMId'],
            'icon': info['RewardTextureName']
        }

with open(os.path.join(base_path, 'CharacterDialogDBSchema.json'), 'r', encoding='utf-8') as f:
    for sen in json.load(f):
        info = sen['Bytes']
        if info['DialogCategory'] != 'UILobby' and info['DialogCategory'] != 'UILobbySpecial':
            continue
        character_id = sen['CharacterId']
        if (chr_info := db_character_dialog.get(character_id, None)) is None:
            chr_info = {
                'UILobby': {},
                'UILobbySpecial': {}
            }
            db_character_dialog[character_id] = chr_info

        if (group := chr_info[info['DialogCategory']].get(info['LocalizeCVGroup'], None)) is None:
            group = []
            chr_info[info['DialogCategory']][info['LocalizeCVGroup']] = group

        group.append({
            'animation': info['AnimationName'],
            'condition': info['DialogCategory'],
            'anniversary': info['Anniversary'],
            'start': info['StartDate'],
            'end': info['EndDate'],
            'type': info['DialogType'],
            'action': info['ActionName'],
            'duration': info['Duration'],
            'textKorean': info['LocalizeKR'],
            'textJapan': info['LocalizeJP'],
            'voice': info['VoiceId']
        })

with open(os.path.join(base_path, 'VoiceSpineDBSchema.json'), 'r', encoding='utf-8') as f:
    for voi in json.load(f):
        paths = [i.split('/') for i in voi['Bytes']['Path']]
        path = [f'{i[-2]}/{i[-1]}.ogg' for i in paths]
        db_voice_spine[voi['Id']] = {
            'path': path,
            'volume': voi['Bytes']['SoundVolume']
        }

with open(os.path.join(base_path, 'VoiceDBSchema.json'), 'r', encoding='utf-8') as f:
    for voi in json.load(f):
        paths = [i.split('/') for i in voi['Bytes']['Path']]
        path = [f'{i[-2]}/{i[-1]}.ogg' for i in paths]
        db_voice[voi['Id']] = {
            'path': path,
            'volume': voi['Bytes']['Volume']
        }

with open(os.path.join(base_path, 'BGMDBSchema.json'), 'r', encoding='utf-8') as f:
    for aud in json.load(f):
        info = aud['Bytes']
        path = info['Path']
        path = [f'{i[i.rindex("/") + 1:]}.ogg' for i in path]
        db_bgm[info['Id']] = {
            'path': path,
            'volume': info['Volume'],
            'loopStart': info['LoopStartTime'],
            'loopEnd': info['LoopEndTime'],
            'transition': info['LoopTranstionTime'],
            'loopOffset': info['LoopOffsetTime']
        }