# Avoid circular imports, by not requiring app to be imported. Allows functions to be used without the Flask wrapper.
from .utils.database import handle_integrity_errors, create_new_workout

from .utils.custom_exceptions import ExerciseDoesNotExistException

from .schemas import CreateWorkoutResponseSchema

from sqlalchemy import exc
from sqlalchemy.orm import Session
from fastapi import HTTPException

def create_workout_raw(
    db_session: Session,
    payload,
    decoded_access_token,
    ai_generated=False,
):

    try:

        workout_id = create_new_workout(
            db_session=db_session,
            user_id=decoded_access_token["user_id"],
            workout_name=payload.name,
            workout_components=payload.workout_components,
            ai_generated=ai_generated,
        )

    # TODO -> Move the catches higher up?
    except exc.IntegrityError as e:
        return handle_integrity_errors(e)
    except ExerciseDoesNotExistException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # TODO -> Refactor so that this is being made by the route itself
    return {
        'message': f'Workout added to DB [Workout ID: {workout_id}]'
    }