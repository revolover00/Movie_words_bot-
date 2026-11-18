"""Curated expressions organised by CEFR level and topic.

CEFR labels are approximate; learner ability and context vary.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

LEVELS = ('A2', 'B1', 'B2', 'C1', 'C2')

@dataclass(frozen=True)
class Phrase:
    text: str
    topic: str

# Short, useful spoken expressions are preferred so they can be matched to
# dialogue clips. Selection is limited to captions actually found on Yarn.
BANK = {
    'A2': [
        Phrase('How are you?', 'greetings'), Phrase('Nice to meet you', 'greetings'),
        Phrase('See you later', 'greetings'), Phrase('I have no idea', 'communication'),
        Phrase('What do you mean?', 'communication'), Phrase('I am not sure', 'communication'),
        Phrase('Take your time', 'support'), Phrase('Are you okay?', 'support'),
        Phrase('Be careful', 'safety'), Phrase('I am hungry', 'food'),
        Phrase('Let me help you', 'help'), Phrase('Where are you going?', 'travel'),
        Phrase('What happened?', 'events'), Phrase('I am sorry', 'feelings'),
        Phrase('That is a good idea', 'ideas'), Phrase('I need a break', 'work'),
        Phrase('I am on my way', 'travel'), Phrase('Can you help me?', 'help'),
        Phrase('What time is it?', 'time'), Phrase('I feel better', 'health'),
    ],
    'B1': [
        Phrase('It is up to you', 'decisions'), Phrase('I changed my mind', 'decisions'),
        Phrase('I cannot wait', 'feelings'), Phrase('I am looking forward to it', 'plans'),
        Phrase('That makes sense', 'communication'), Phrase('I did not mean that', 'communication'),
        Phrase('I am running late', 'time'), Phrase('I will figure it out', 'problems'),
        Phrase('I am proud of you', 'relationships'), Phrase('You have a point', 'discussion'),
        Phrase('Keep an eye on him', 'safety'), Phrase('I need to think', 'decisions'),
        Phrase('Let us get started', 'work'), Phrase('Do not give up', 'motivation'),
        Phrase('That is not fair', 'feelings'), Phrase('We are in trouble', 'problems'),
        Phrase('I will be right back', 'travel'), Phrase('It is worth a try', 'ideas'),
        Phrase('I do not feel well', 'health'), Phrase('You made my day', 'relationships'),
    ],
    'B2': [
        Phrase('Let us get to the point', 'communication'), Phrase('I will keep that in mind', 'communication'),
        Phrase('It slipped my mind', 'memory'), Phrase('We are on the same page', 'work'),
        Phrase('That is out of the question', 'decisions'), Phrase('I am having second thoughts', 'decisions'),
        Phrase('You are missing the point', 'discussion'), Phrase('I owe you one', 'relationships'),
        Phrase('Do not take it personally', 'relationships'), Phrase('Let us call it a day', 'work'),
        Phrase('We need to clear the air', 'relationships'), Phrase('I will take care of it', 'responsibility'),
        Phrase('You are in good hands', 'support'), Phrase('We are running out of time', 'time'),
        Phrase('I cannot make up my mind', 'decisions'), Phrase('I have a lot on my mind', 'feelings'),
        Phrase('That is easier said than done', 'problems'), Phrase('It is not what it looks like', 'communication'),
        Phrase('We have a lot in common', 'relationships'), Phrase('There is more to it', 'ideas'),
    ],
    'C1': [
        Phrase('Let us cut to the chase', 'communication'), Phrase('That is beside the point', 'discussion'),
        Phrase('It is a blessing in disguise', 'life'), Phrase('I beg to differ', 'discussion'),
        Phrase('You are jumping to conclusions', 'judgment'), Phrase('Let us agree to disagree', 'discussion'),
        Phrase('I am in two minds', 'decisions'), Phrase('We are in the same boat', 'support'),
        Phrase('Do not beat around the bush', 'communication'), Phrase('It is a long shot', 'risk'),
        Phrase('That is the last straw', 'feelings'), Phrase('You have crossed the line', 'relationships'),
        Phrase('I will take your word for it', 'trust'), Phrase('Let us not get carried away', 'judgment'),
        Phrase('There is no point in arguing', 'discussion'), Phrase('I am at a loss', 'feelings'),
        Phrase('It is a matter of time', 'time'), Phrase('We have our work cut out for us', 'work'),
        Phrase('I have my reservations', 'decisions'), Phrase('Take it with a grain of salt', 'judgment'),
    ],
    'C2': [
        Phrase('The ball is in your court', 'decisions'), Phrase('It is a double-edged sword', 'risk'),
        Phrase('That is a moot point', 'discussion'), Phrase('The jury is still out', 'judgment'),
        Phrase('You are barking up the wrong tree', 'problems'), Phrase('We are treading on thin ice', 'risk'),
        Phrase('It is a slippery slope', 'risk'), Phrase('That is a tall order', 'work'),
        Phrase('Let us play devil\'s advocate', 'discussion'), Phrase('It is a foregone conclusion', 'decisions'),
        Phrase('That is a blessing in disguise', 'life'), Phrase('We are at a crossroads', 'decisions'),
        Phrase('You have opened a can of worms', 'problems'), Phrase('The writing is on the wall', 'judgment'),
        Phrase('I would not hold my breath', 'expectations'), Phrase('It is a double whammy', 'problems'),
        Phrase('That is a bit of a stretch', 'discussion'), Phrase('There is no silver bullet', 'solutions'),
        Phrase('That is a bitter pill to swallow', 'feelings'), Phrase('It is a necessary evil', 'life'),
    ],
}


def candidates(level: str, seen: set[str], recent_topics: list[str]) -> list[Phrase]:
    """Prefer unseen expressions and topics, then recycle after exhaustion."""
    bank = BANK[level]
    pool = [p for p in bank if p.text.casefold() not in seen] or list(bank)
    pool = list(pool)
    random.shuffle(pool)
    return sorted(pool, key=lambda p: p.topic in recent_topics[:3])
