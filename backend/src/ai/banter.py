"""
Event-driven bot banter.

Makes opponents feel alive by reacting to what just happened — winning a big
pot, busting out, doubling up, or going on tilt after a beat. Lines are
personality-flavoured and bilingual, emitted via the existing ai_thought
channel.
"""
from __future__ import annotations

import random
from typing import Optional

# event -> locale -> personality (or '_') -> list of lines
_BANTER: dict[str, dict[str, dict[str, list[str]]]] = {
    'won_big': {
        'en': {
            'maniac': ["SHIP IT!! 🚀", "That's how it's done!", "Easy game, easy life."],
            'shark': ["Thanks for the chips.", "Calculated.", "Ship it."],
            'rock': ["Finally, a hand worth playing.", "Patience pays."],
            'tag': ["Value, baby.", "Read you like a book."],
            'station': ["Ooh, I won? Nice!", "Lucky me!"],
            '_': ["Stacked!", "Mine now.", "Good pot."],
        },
        'zh': {
            'maniac': ["全收了!! 🚀", "就这？太简单了！", "这就是实力。"],
            'shark': ["谢谢送的筹码。", "都在算计之中。", "收下了。"],
            'rock': ["终于来了手好牌。", "耐心总有回报。"],
            'tag': ["价值满满。", "你的牌我一眼看穿。"],
            'station': ["哦我赢了？爽！", "运气不错！"],
            '_': ["筹码到手！", "这池归我了。", "好池。"],
        },
    },
    'lost_big': {
        'en': {
            'maniac': ["You got LUCKY.", "Rigged. Absolutely rigged.", "I'll get it all back."],
            'rock': ["...unbelievable.", "How do you call that?"],
            '_': ["Ugh.", "Nice hand.", "I had it until the river..."],
        },
        'zh': {
            'maniac': ["你就是走运！", "这牌有问题，绝对有问题。", "我会全部赢回来的。"],
            'rock': ["……难以置信。", "这种牌你也跟？"],
            '_': ["唉。", "好牌。", "河牌前我都是赢的……"],
        },
    },
    'eliminated': {
        'en': {
            'maniac': ["I'll be back. Count on it.", "Variance. Pure variance."],
            'rock': ["Well played. I'm out.", "That's poker."],
            '_': ["GG. I'm done.", "Out. Nice game.", "Busted. See you."],
        },
        'zh': {
            'maniac': ["我会回来的，等着。", "纯属运气，纯属运气。"],
            'rock': ["打得不错，我出局了。", "这就是扑克。"],
            '_': ["GG，我出局了。", "下桌了，承让。", "破产，回见。"],
        },
    },
    'doubled_up': {
        'en': {'_': ["Back in business!", "Double up, let's go.", "Now we're talking."]},
        'zh': {'_': ["满血复活！", "翻倍了，来吧。", "这才像话。"]},
    },
}


def get_banter(event: str, personality: str, locale: str = 'en') -> Optional[str]:
    """Return a random banter line for an event, or None if none defined."""
    by_locale = _BANTER.get(event, {})
    pools = by_locale.get(locale) or by_locale.get('en') or {}
    lines = pools.get(personality) or pools.get('_')
    if not lines:
        return None
    return random.choice(lines)
