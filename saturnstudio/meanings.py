"""
Meanings library for the built-in chart reading.

Written for Where Is Saturn? in plain, warm language. Astrology is a reflective tradition,
not a science: these texts describe tendencies and invitations, never fixed fate.
"""
from __future__ import annotations

# ─── Signs ──────────────────────────────────────────────────────────────────
# style: how a placement in this sign tends to act ("…works {style}")
SIGNS = {
    "Aries": {
        "element": "Fire", "quality": "Cardinal", "ruler": "Mars",
        "style": "boldly and directly, first to act and quick to begin",
        "gift": "courage and the spark that starts things",
        "edge": "impatience and acting before listening",
    },
    "Taurus": {
        "element": "Earth", "quality": "Fixed", "ruler": "Venus",
        "style": "steadily and sensually, building slowly toward what lasts",
        "gift": "patience, loyalty and a talent for making things real",
        "edge": "stubbornness and holding on too long",
    },
    "Gemini": {
        "element": "Air", "quality": "Mutable", "ruler": "Mercury",
        "style": "curiously and quickly, through words, questions and connections",
        "gift": "wit, adaptability and a bright, open mind",
        "edge": "scattered focus and restlessness",
    },
    "Cancer": {
        "element": "Water", "quality": "Cardinal", "ruler": "Moon",
        "style": "protectively and intuitively, through care and belonging",
        "gift": "deep empathy and the power to make others feel at home",
        "edge": "moodiness and retreating into your shell",
    },
    "Leo": {
        "element": "Fire", "quality": "Fixed", "ruler": "Sun",
        "style": "warmly and generously, from the heart and in full view",
        "gift": "creative fire, loyalty and a talent for lifting others",
        "edge": "pride and needing applause",
    },
    "Virgo": {
        "element": "Earth", "quality": "Mutable", "ruler": "Mercury",
        "style": "carefully and usefully, refining everything it touches",
        "gift": "skill, discernment and quiet devotion to service",
        "edge": "perfectionism and harsh self-criticism",
    },
    "Libra": {
        "element": "Air", "quality": "Cardinal", "ruler": "Venus",
        "style": "gracefully and diplomatically, always seeking balance",
        "gift": "fairness, charm and a gift for partnership",
        "edge": "indecision and keeping the peace at your own cost",
    },
    "Scorpio": {
        "element": "Water", "quality": "Fixed", "ruler": "Pluto and Mars",
        "style": "intensely and privately, all the way to the depths",
        "gift": "loyalty, insight and the power to transform",
        "edge": "control, suspicion and holding grudges",
    },
    "Sagittarius": {
        "element": "Fire", "quality": "Mutable", "ruler": "Jupiter",
        "style": "freely and expansively, always searching for meaning",
        "gift": "optimism, honesty and a hunger for truth",
        "edge": "restlessness and promising more than you can give",
    },
    "Capricorn": {
        "element": "Earth", "quality": "Cardinal", "ruler": "Saturn",
        "style": "patiently and ambitiously, climbing toward lasting achievement",
        "gift": "discipline, responsibility and quiet authority",
        "edge": "rigidity and carrying every burden alone",
    },
    "Aquarius": {
        "element": "Air", "quality": "Fixed", "ruler": "Uranus and Saturn",
        "style": "independently and inventively, with one eye on the future",
        "gift": "originality, fairness and loyalty to the greater good",
        "edge": "detachment and resisting closeness",
    },
    "Pisces": {
        "element": "Water", "quality": "Mutable", "ruler": "Neptune and Jupiter",
        "style": "fluidly and compassionately, through imagination and feeling",
        "gift": "empathy, creativity and spiritual depth",
        "edge": "escapism and blurred boundaries",
    },
}

# ─── Big three: hand-written ────────────────────────────────────────────────
SUN = {
    "Aries": "You were born to begin. Your spirit comes alive in the first step, the open road, the challenge nobody else will take. Life asks you to be brave and to lead, and to learn that real strength includes patience.",
    "Taurus": "Your light burns slow and steady, like a hearth fire. You are here to build something real and lasting, to savour the body and the senses, and to trust your own pace in a hurried world.",
    "Gemini": "You are a messenger. Your vitality comes from questions, conversations and the flash of a new idea. You are here to connect people and ideas, and to find the thread of meaning among your many interests.",
    "Cancer": "You shine by sheltering. Home, family and the people you claim as your own are the centre of your world. You are here to nourish, to remember, and to let your sensitive heart be a strength.",
    "Leo": "The Sun rules your sign, and you were born to radiate. Creativity, play and generous love are your nature. You are here to shine wholeheartedly and to help others find the courage to shine too.",
    "Virgo": "You find meaning in doing things well. Your spirit comes alive in craft, service and the careful improvement of the world around you. You are here to heal and refine, and to be as kind to yourself as you are useful to others.",
    "Libra": "You come alive in relationship. Beauty, fairness and harmony are sacred to you. You are here to build bridges between people and to learn that true balance includes your own needs.",
    "Scorpio": "You live at depth. Surface answers never satisfy you. You are drawn to truth, intimacy and transformation. You are here to face what others avoid and to rise, again and again, renewed.",
    "Sagittarius": "You are a seeker. Freedom, travel, philosophy and a good laugh keep your fire burning. You are here to explore, to teach what you discover, and to keep faith in a bigger picture.",
    "Capricorn": "You are the mountain climber of the zodiac. Your spirit grows through purpose, responsibility and patient effort. You are here to build a legacy and to discover that you are worthy before you achieve anything.",
    "Aquarius": "You are here to think differently. Your light shines through originality, friendship and a vision of a fairer future. You are here to be yourself without apology and to bring the group forward with you.",
    "Pisces": "You are a dreamer and a mystic. You feel the unseen currents that connect all living things. You are here to create, to heal and to love without limit, while learning where you end and others begin.",
}

MOON = {
    "Aries": "You feel quickly and fiercely. Your emotions flare and pass like fire. You feel safest when you are free to act, and you need honest, direct people who don't make you wait.",
    "Taurus": "The Moon is exalted in Taurus, so your emotional nature is steady and grounded. Comfort, good food, touch and routine soothe you. You need loyalty, and you give it richly in return.",
    "Gemini": "You process feelings by talking and thinking them through. Curiosity calms you, and boredom unsettles you. You need conversation, variety and people who delight in your mind.",
    "Cancer": "The Moon is at home in Cancer, so your feelings run deep and tender. Home, family and memory are your emotional anchors. You need to feel you belong, and you create belonging for others.",
    "Leo": "Your heart is warm and wants to be seen. Affection, appreciation and play restore you. You need to know you matter, and you love with loyal, radiant generosity.",
    "Virgo": "You care through practical help. Order, useful work and quiet routines calm your mind. You need to feel competent and useful, and to learn that you don't have to earn rest.",
    "Libra": "You find emotional peace in harmony and good company. Beauty and fairness soothe you, and conflict unsettles you. You need partnership, and you need to hear your own voice within it.",
    "Scorpio": "Your feelings are oceanic and private. You sense what others hide. You need deep trust and real intimacy, and your emotional life is a path of powerful renewal.",
    "Sagittarius": "Your spirit needs room to roam. Adventure, laughter and big ideas lift your mood. You need freedom and honesty, and a sense that life is going somewhere meaningful.",
    "Capricorn": "You hold your feelings with dignity and self-control. Structure and accomplishment steady you. You need respect and security, and permission to lean on others too.",
    "Aquarius": "You feel at ease with a little distance and a lot of freedom. Friendship and shared ideals nourish you. You need to be accepted exactly as you are, quirks and all.",
    "Pisces": "Your emotional world is vast, porous and compassionate. Music, art, nature and solitude restore you. You need gentle boundaries and time to return to yourself.",
}

RISING = {
    "Aries": "You meet life head-on. Others see energy, directness and courage. You come across as someone who gets things started, and you learn best by doing.",
    "Taurus": "You meet life calmly and steadily. Others see a grounded, reliable presence with a love of comfort and beauty. You prefer to move at your own pace.",
    "Gemini": "You meet life with curiosity. Others see a quick, friendly, talkative mind. You adapt fast and are drawn to learning, news and connection.",
    "Cancer": "You meet life with care and caution. Others sense warmth and a protective instinct. You open up once you feel safe, and you make others feel at home.",
    "Leo": "You meet life with warmth and presence. Others notice you when you walk in. Your natural confidence and generosity invite people to gather around you.",
    "Virgo": "You meet life thoughtfully and precisely. Others see someone capable, modest and observant. You notice the details and quietly make things work better.",
    "Libra": "You meet life with grace and diplomacy. Others see charm, good taste and a wish to be fair. You naturally smooth tensions and bring people together.",
    "Scorpio": "You meet life with watchful intensity. Others sense depth, magnetism and privacy. You reveal yourself slowly and see through pretence quickly.",
    "Sagittarius": "You meet life as an adventure. Others see optimism, humour and frankness. You are drawn to wide horizons, new ideas and people from far away.",
    "Capricorn": "You meet life seriously and with self-possession. Others see maturity and competence, often beyond your years. You are built for the long climb.",
    "Aquarius": "You meet life as an original. Others see someone friendly but independent, a little unconventional and ahead of their time.",
    "Pisces": "You meet life softly and intuitively. Others see gentleness, imagination and empathy. You absorb the moods around you and need time to recover your own.",
}

# ─── Points ─────────────────────────────────────────────────────────────────
# label, domain (long), short word, kind: luminary | personal | social | outer | point | angle
POINTS = {
    "Sun": ("Sun", "your core self, will and vitality", "identity", "luminary"),
    "Moon": ("Moon", "your emotional needs, instincts and sense of safety", "feelings", "luminary"),
    "Mercury": ("Mercury", "how you think, learn and speak", "mind", "personal"),
    "Venus": ("Venus", "how you love, what you value and what you find beautiful", "heart", "personal"),
    "Mars": ("Mars", "your drive, desire and courage", "drive", "personal"),
    "Jupiter": ("Jupiter", "where you grow, find faith and meet good fortune", "growth", "social"),
    "Saturn": ("Saturn", "where you meet discipline, time and hard-won mastery", "discipline", "social"),
    "Uranus": ("Uranus", "where you break patterns and claim your freedom", "freedom", "outer"),
    "Neptune": ("Neptune", "your dreams, intuition and longing for the sacred", "dreams", "outer"),
    "Pluto": ("Pluto", "where you face power and deep transformation", "transformation", "outer"),
    "True_North_Lunar_Node": ("North Node", "the direction your soul is growing toward", "destiny", "point"),
    "Mean_North_Lunar_Node": ("North Node (mean)", "the direction your soul is growing toward", "destiny", "point"),
    "True_South_Lunar_Node": ("South Node", "the gifts and habits you arrive with", "the past", "point"),
    "Mean_South_Lunar_Node": ("South Node (mean)", "the gifts and habits you arrive with", "the past", "point"),
    "Chiron": ("Chiron", "your deepest wound and the healing you can offer others", "healing", "point"),
    "Mean_Lilith": ("Black Moon Lilith", "your untamed nature and where you refuse to be controlled", "wildness", "point"),
    "True_Lilith": ("Lilith (true)", "your untamed nature and where you refuse to be controlled", "wildness", "point"),
    "Ceres": ("Ceres", "how you nurture and need to be nurtured", "nurture", "point"),
    "Pallas": ("Pallas", "your strategic wisdom and creative intelligence", "wisdom", "point"),
    "Juno": ("Juno", "what you need in committed partnership", "commitment", "point"),
    "Vesta": ("Vesta", "what you hold sacred and devote yourself to", "devotion", "point"),
    "Pars_Fortunae": ("Part of Fortune", "where joy and ease come most naturally", "fortune", "point"),
    "Vertex": ("Vertex", "fated meetings and turning points", "fate", "point"),
    "Ascendant": ("Ascendant", "how you meet the world", "approach", "angle"),
    "Medium_Coeli": ("Midheaven", "your calling and public path", "calling", "angle"),
    "Descendant": ("Descendant", "what you seek in close partners", "partnership", "angle"),
    "Imum_Coeli": ("IC", "your roots, home and private foundation", "roots", "angle"),
}

PLANET_ORDER = list(POINTS)

# ─── Houses ─────────────────────────────────────────────────────────────────
HOUSES = {
    1: ("Self", "the body, appearance, first impressions and new beginnings"),
    2: ("Resources", "money, possessions, talents and self-worth"),
    3: ("Mind & Kin", "learning, speech, siblings, neighbours and short journeys"),
    4: ("Home & Roots", "home, family, ancestry and inner foundations"),
    5: ("Joy & Creation", "creativity, romance, children, play and self-expression"),
    6: ("Work & Health", "daily work, routines, service and wellbeing"),
    7: ("Partnership", "marriage, close partners, contracts and open rivals"),
    8: ("Depth & Shared Wealth", "intimacy, shared money, inheritance and transformation"),
    9: ("Wisdom & Travel", "belief, higher learning, publishing and long journeys"),
    10: ("Calling", "career, reputation, ambition and public standing"),
    11: ("Community", "friends, groups, networks and hopes for the future"),
    12: ("The Unseen", "solitude, the unconscious, spirituality and what is hidden"),
}

ORDINAL = {1: "1st", 2: "2nd", 3: "3rd", 21: "21st", 22: "22nd", 23: "23rd"}


def ordinal(n: int) -> str:
    return ORDINAL.get(n, f"{n}th")


# ─── Aspects ────────────────────────────────────────────────────────────────
ASPECTS = {
    "conjunction": ("Conjunction", "fuse", "{a} and {b} act as one force. Their energies amplify each other, so learn to tell them apart when you need to.", "intense"),
    "opposition": ("Opposition", "face each other", "{a} and {b} pull from opposite ends. Balance comes through awareness, and often through other people mirroring one side back to you.", "challenging"),
    "square": ("Square", "clash", "{a} and {b} create friction. This tension is uncomfortable, but it is also the engine of your growth and achievement.", "challenging"),
    "trine": ("Trine", "flow together", "{a} and {b} cooperate with ease. This is a natural talent, so use it on purpose rather than taking it for granted.", "harmonious"),
    "sextile": ("Sextile", "support each other", "{a} and {b} open doors for each other. The opportunity is real, but it asks you to take the first step.", "harmonious"),
    "quincunx": ("Quincunx", "need adjusting", "{a} and {b} speak different languages. Growth comes through small, patient adjustments.", "challenging"),
    "semi-sextile": ("Semi-sextile", "brush against each other", "{a} and {b} are neighbours with different habits, and a subtle awareness helps them work together.", "harmonious"),
    "semi-square": ("Semi-square", "irritate each other", "{a} and {b} create a small but persistent friction that asks for attention.", "challenging"),
    "sesquiquadrate": ("Sesquiquadrate", "unsettle each other", "{a} and {b} create restless tension that rewards steady effort.", "challenging"),
    "quintile": ("Quintile", "spark creativity", "{a} and {b} combine into a creative, individual talent.", "harmonious"),
    "biquintile": ("Biquintile", "spark creativity", "{a} and {b} combine into a creative, individual talent.", "harmonious"),
}

# ─── Balance ────────────────────────────────────────────────────────────────
ELEMENT_STRONG = {
    "fire": "Fire leads your chart. You run on enthusiasm, inspiration and courage, and you need purpose and movement to feel alive.",
    "earth": "Earth leads your chart. You are practical, patient and grounded, and you trust what you can touch, build and prove.",
    "air": "Air leads your chart. You live through ideas, conversation and connection, and you need mental space and good company.",
    "water": "Water leads your chart. You are guided by feeling, intuition and empathy, and you need emotional truth and closeness.",
}
ELEMENT_WEAK = {
    "fire": "Fire is quiet in your chart. Motivation may need deliberate kindling, so seek out movement, sunlight and people who inspire you.",
    "earth": "Earth is quiet in your chart. Grounding may not come naturally, so routines, the body and nature help you stay anchored.",
    "air": "Air is quiet in your chart. Stepping back to name and discuss what you feel can bring welcome perspective.",
    "water": "Water is quiet in your chart. Feelings may be easier to think about than to feel, so gentle reflection and trusted company help.",
}
QUALITY_STRONG = {
    "cardinal": "Cardinal energy is strongest, so you are an initiator who likes to start, lead and set things in motion.",
    "fixed": "Fixed energy is strongest, so you are a sustainer, loyal and determined, and able to see things through.",
    "mutable": "Mutable energy is strongest, so you are adaptable, able to change course and happy to learn as you go.",
}

# ─── Moon phase at birth (after Dane Rudhyar's lunation types) ─────────────
MOON_PHASE = {
    "New Moon": "Born at the New Moon, you are a pioneer of your own life, acting on instinct and starting fresh without a map.",
    "Waxing Crescent": "Born under a Waxing Crescent, you push forward against the pull of the past, determined to grow something new.",
    "First Quarter": "Born at the First Quarter, you are a builder in a crisis of action who thrives on challenge and decisive moves.",
    "Waxing Gibbous": "Born under a Waxing Gibbous Moon, you refine and perfect, always asking how something could be better.",
    "Full Moon": "Born at the Full Moon, you see clearly through relationships, seeking to bring opposing forces into awareness and balance.",
    "Waning Gibbous": "Born under a Waning Gibbous Moon, you are a sharer and teacher who is moved to pass on what you have learned.",
    "Last Quarter": "Born at the Last Quarter, you question old structures and are ready to let go of what no longer serves.",
    "Waning Crescent": "Born under a Waning Crescent, you carry a visionary, old-soul quality and are here to complete a cycle and seed the next.",
}

# ─── Transits and returns ───────────────────────────────────────────────────
TRANSIT_FORCE = {
    "Sun": "brings attention and vitality for a few days",
    "Moon": "colours your mood for a few hours",
    "Mercury": "stirs thoughts, talks and plans",
    "Venus": "brings pleasure, affection and a softer touch",
    "Mars": "adds heat, drive and sometimes impatience",
    "Jupiter": "opens doors and invites growth, optimism and generosity",
    "Saturn": "asks for structure, patience and honest effort, and rewards what is built to last",
    "Uranus": "brings awakening, surprise and a hunger for freedom",
    "Neptune": "dissolves old forms, inviting imagination, compassion and surrender, so watch for confusion",
    "Pluto": "brings slow, deep transformation, where what ends makes room for rebirth",
    "True_North_Lunar_Node": "points to a new direction and fated meetings",
    "Mean_North_Lunar_Node": "points to a new direction and fated meetings",
    "Chiron": "touches old wounds so they can heal",
}

DISCLAIMER = (
    "Astrology is a reflective tradition, not a science. Use this reading for self-reflection, "
    "not for medical, legal, financial or other major decisions."
)
