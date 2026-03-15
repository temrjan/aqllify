from pydantic import BaseModel


class Phrase(BaseModel):
    uzbek: str
    russian: str
    audio_url: str | None = None


class Exercise(BaseModel):
    type: str            # open_translate, reverse_translate, fill_blank, build_sentence, choice, dialog_reply, spiral, listen_write
    prompt: str
    answer_context: str | None = None
    answer: str | None = None
    words: list[str] | None = None
    options: list[str] | None = None
    correct: int | None = None
    bot_says: str | None = None
    context: str | None = None
    uses_lessons: list[int] | None = None
    xp: int = 10


class LessonMeta(BaseModel):
    title: str
    block: int
    lesson: int
    new_phrases: int
    spiral_from: list[int] = []
    level: str = 'spark'
    xp_reward: int = 50


class GrammarTip(BaseModel):
    text: str


class MiniDialog(BaseModel):
    lines: list[str]


class Homework(BaseModel):
    text: str


class LessonContent(BaseModel):
    meta: LessonMeta
    slug: str
    phrases: list[Phrase]
    grammar: list[GrammarTip]
    dialog: MiniDialog | None = None
    homework: Homework | None = None
    exercises: list[Exercise]


class LessonListItem(BaseModel):
    slug: str
    title: str
    block: int
    lesson: int
    completed: bool = False
    score: float | None = None
