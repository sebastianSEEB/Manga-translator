from pydantic import BaseModel, Field, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Translation(StrictModel):
    id: str = Field(max_length=30)
    en: str = Field(max_length=1500)
    kind: str = Field(pattern="^(dialogue|caption|sfx)$")

class TranslationBatch(StrictModel):
    translations: list[Translation] = Field(max_length=80)

class Word(StrictModel):
    surface: str = Field(max_length=200)
    reading: str = Field(max_length=200)
    meaning: str = Field(max_length=500)
    part_of_speech: str = Field(max_length=100)

class Lesson(StrictModel):
    reading: str = Field(max_length=3000)
    words: list[Word] = Field(max_length=200)
    grammar: str = Field(max_length=3000)
