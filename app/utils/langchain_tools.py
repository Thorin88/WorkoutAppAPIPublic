from .database import get_known_workout_names, get_latest_finished_workouts_for_user
from ..route_functions import create_workout_raw
from ..schemas import CreateWorkoutSchema

from langchain.tools import tool
from typing import List, Dict, Any

from ..database import SessionLocal

# TODO -> If this works, move to a different file
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# Once annotated as a tool, this doesn't work like a regular function anymore. Hence this is just essentially a decorator
# that preserves the original function.
@tool
def get_known_workout_names_tool() -> List[str]:
    """
    Gets the names of all exercises that the backend is aware of. Workout recommendations
    should only include names from this list.
    """

    db_gen = get_db()
    db_session = next(db_gen)
    try:
        result = get_known_workout_names(db_session=db_session)
    finally:
        db_gen.close()

    return result

@tool
def create_workout_recommendation_tool(
    user_id : str,
    workout_name : str,
    workout_components : List[Dict[str, Any]],
) -> None:
    """
    Registers a list of workout components. Each component follows this schema:

    {
        "exercise_name" : str. The name of the exercise,
        "position" : int. Starts from 0. The position of the exercise in the workout,
        "reps" : str. The number of reps to perform. Can be a single number or a rep range,
        "weight" : float. The weight to use,
        "units" : str. kg or lbs, indicating the weight units,
    }

    The user_id will be provided to you.

    """

    # create_workout_recommendation(payload=, decoded_access_token=)

    payload = {
        "name" : workout_name,
        "workout_components" : workout_components,
        # TODO -> Currently ignored in favour of parameter. Arose due to tight coupling of the data classes
        # for the API response for creation and retrieval for workout objects on mobile side (needs to be changed)
        "ai_generated" : True,
    }

    db_gen = get_db()
    db_session = next(db_gen)
    try:
        result = create_workout_raw(
            payload=CreateWorkoutSchema(**payload),
            decoded_access_token={"user_id" : user_id},
            ai_generated=True,
            db_session=db_session,
        )
    finally:
        db_gen.close()

    return result

@tool
def get_past_5_workouts_tool(
    user_id : str,
) -> None:
    """
    Returns a list of the user's 5 most recently completed workouts.

    The user_id to use with this tool will be provided to you.
    """

    # create_workout_recommendation(payload=, decoded_access_token=)

    db_gen = get_db()
    db_session = next(db_gen)
    try:
        workouts = get_latest_finished_workouts_for_user(
            db_session=db_session,
            user_id=user_id,
        )
    finally:
        db_gen.close()

    return workouts