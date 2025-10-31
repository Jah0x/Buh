from aiogram.fsm.state import State, StatesGroup


class ReleaseStates(StatesGroup):
    track_upload = State()
    cover_upload = State()
    full_name = State()
    email = State()
    consent = State()
    track_name = State()
    artist = State()
    authors = State()
    description = State()
    release_date = State()


class ConsentStates(StatesGroup):
    confirmation = State()
