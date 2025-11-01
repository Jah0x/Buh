from aiogram.fsm.state import State, StatesGroup
class ReleaseStates(StatesGroup):
    service = State()
    track_upload = State()
    cover_upload = State()
    artist_name = State()
    release_title = State()
    genre = State()
    socials = State()
    contact_email = State()


class MenuStates(StatesGroup):
    pc = State()
    courses = State()
    studios = State()
    links = State()


class PCBuildStates(StatesGroup):
    budget = State()
    goals = State()
    wishes = State()
