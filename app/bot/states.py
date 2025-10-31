"""Finite state machines for user flows."""
from aiogram.fsm.state import State, StatesGroup


class ReleaseStates(StatesGroup):
    track_upload = State()
    cover_upload = State()
    track_name = State()
    artist = State()
    authors = State()
    description = State()
    release_date = State()
    full_name = State()
    email = State()
    consent = State()
    payment = State()
    contract = State()


class ConsentStates(StatesGroup):
    confirmation = State()
