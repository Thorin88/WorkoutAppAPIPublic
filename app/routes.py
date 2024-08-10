from fastapi import Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse 
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from typing import Annotated

from app import app

from .database import SessionLocal, engine
from . import models

from sqlalchemy import exc

import jwt
import json
import os
from datetime import timedelta

from .schemas import (
    BasePOSTResponse, BaseErrorResponse,
    NewUserSchema,
    SaltResponseSchema,
    LoginRequestSchema, LoginResponseSchema,
    AccessTokenResponseSchema,
    CreateWorkoutSchema,
    WorkoutRecommendationRequestSchema, WorkoutRecommendationResponseSchema,
    SavedWorkoutsResponseSchema,
    UpdateComponentsSchema, RetrievedWorkoutComponentSchema,
    FinishWorkoutSchema,
)
# These need to be imported in order to be visible to functions like db.create_all
from .models import Users, UserPasswordHashes, WorkoutComponentHistory, FinishedWorkouts, FinishedWorkoutComponents
from .utils.database import (
    create_new_workout, handle_integrity_errors, generic_add_to_table,
    attempt_insert_new_user,login_user, populate_base_tables,
    get_workouts_for_user,
)
from .utils.jwt import (
    generate_jwt, verify_jwt, verify_jwt_throws,
    requires_authorization,
)
from .utils.logging import (
    log_action,
    SUCCESSFUL_LOG_IN, UNSUCCESSFUL_LOG_IN, LOGGED_OUT,
)
from .utils.custom_exceptions import ExerciseDoesNotExistException, UsernameAlreadyExistsException, UsernameDoesNotExistException
from .route_functions import create_workout_raw
from .utils.langchain import simple_prompt

class EnvironmentPermissionError(Exception):
    pass

# new_user_schema = NewUserSchema()
# salt_request_schema = SaltRequestSchema()
# salt_response_schema = SaltResponseSchema()
# login_request_schema = LoginRequestSchema()
# access_token_request_schema = AccessTokenRequestSchema()
# create_workout_schema = CreateWorkoutSchema()
# recommendation_request_schema = WorkoutRecommendationRequestSchema()
# workouts_saved_response_schema = WorkoutsSavedResponseSchema()
# update_components_schema = RetrievedWorkoutComponentSchema(many=True)

# Dependancy. Used to get a database connection
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# # Modifies how these exceptions are handled, using 'message' instead of 'detail'.
# https://fastapi.tiangolo.com/tutorial/handling-errors/
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code, 
        content={
            "message" : exc.detail,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("[RequestValidationError]", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "message" : exc.errors(),
        },
    )

# TODO
# @app.route('/')
# def home():
#     """
#     API's base URL
#     """
#     return {'message': 'OK'}, 200

@app.post('/create_tables', status_code=201, tags=["temp"])
def create_tables(db_session: Session = Depends(get_db)):

    try:

        models.Base.metadata.create_all(bind=engine)

        populate_base_tables(db_session=db_session)

    except (Exception) as e:
        return {'message': str(e)}, 500

    return {'message': 'Database tables created, or already existed.'}, 200

# TODO -> Don't just use GET and POST, there are other words for deletion/change endpoints
@app.post('/drop_tables', status_code=201, tags=["temp"])
def drop_tables(db_session: Session = Depends(get_db)):

    try:
        # Only allow the API to drop tables if being run in certain environments
        envs_allowed = ["dev", "debug"]
        if os.environ["ENV"] in envs_allowed:
            models.Base.metadata.drop_all(bind=engine)
            db_session.commit()
        else:
            raise EnvironmentPermissionError(f"Cannot drop tables outside of the following environments: {envs_allowed}")
    except (EnvironmentPermissionError) as e:
        return {'message': str(e)}, 403
    except (Exception) as e:
        return {'message': str(e)}, 500

    return {'message': 'Database tables dropped, and/or tables already did not exist.'}, 200

# TODO -> response model
@app.post(
    '/users/signup',
    status_code=201,
    responses={
        409: {"model": BaseErrorResponse, "description" : "Username already exists"},
    },
    tags=["auth"],
)
def signup(
    payload: NewUserSchema,
    db_session: Session = Depends(get_db),
):

    try:
        
        user_id = attempt_insert_new_user(payload, db_session=db_session)
    except exc.IntegrityError as e:
        raise handle_integrity_errors(e)
    except UsernameAlreadyExistsException as e:
        # TODO -> Return in a nicer format for app to know this was the issue
        raise HTTPException(status_code=409, detail=str(e))
    # Catching this in the generic block will result in the HTTPException being wrapped in an extra layer of HTTPException
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # TODO -> Response object
    return {'message': f'User added to DB [User ID: {user_id}]'}

# https://fastapi.tiangolo.com/tutorial/response-model/
# https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# Full Query setup: Annotated[str | None, Query(max_length=50)] = None, where we have [parameter type (such as None), restricts] = default_value
@app.get(
    '/users/salt',
    response_model=BasePOSTResponse[SaltResponseSchema],
    status_code=200,
    responses={
        # These don't seem to have their schemas enforced, more just a documentation bonus
        404: {"model": BaseErrorResponse, "description" : "Username provided does not exist"},
    },
    tags=["auth"],
)
def get_salt(
    username: Annotated[
        str,
        Query(
            example="Thorin",
            description="Username to get the salt for",
        ),
    ],
    db_session: Session = Depends(get_db),
):

    # TODO -> Refactor this
    try:
        requestedUsername = username
        results = (
            db_session
            .query(Users, UserPasswordHashes)
            .filter(Users.user_id == UserPasswordHashes.user_id)
            .filter(Users.username == requestedUsername)
            .first()
        )
        if results is None:
            raise HTTPException(status_code=404, detail="Username doesn't exist")
        # Make this [1] access safer
        found_salt = results[1]

    # Catching this in the generic block will result in the HTTPException being wrapped in an extra layer of HTTPException
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # FastAPI is able to work with ORM results, so this just works
    return {
        "payload" : found_salt,
    }

@app.post(
    '/users/login',
    response_model=BasePOSTResponse[LoginResponseSchema],
    status_code=201,
    responses={
        403: {"model": BaseErrorResponse, "description" : "Wrong username or password"},
        404: {"model": BaseErrorResponse, "description" : "Username does not exist"},
    },
    tags=["auth"],
)
def login(
    payload: LoginRequestSchema,
    db_session: Session = Depends(get_db),
):

    # TODO -> Refactor
    try:
        
        is_password_correct, useful_user_info = login_user(payload, db_session=db_session)

        action_name = SUCCESSFUL_LOG_IN if is_password_correct else UNSUCCESSFUL_LOG_IN
        log_action(
            action_name=action_name,
            username=payload.username, # useful_user_info is only available if password was correct
            db_session=db_session,
        )

        if not is_password_correct:
            raise HTTPException(status_code=403, detail=f'Wrong username or password')
        
        token = generate_jwt(token_lifetime=timedelta(minutes=15), **useful_user_info)

        payload_contents = LoginResponseSchema(
            refresh_token=token,
        )
        
        return {
            'payload': payload_contents,
         }
        
    except UsernameDoesNotExistException as e:
        # Cannot log this without a known username
        raise HTTPException(status_code=404, detail=str(e))
    # Catching this in the generic block will result in the HTTPException being wrapped in an extra layer of HTTPException
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    '/access_tokens',
    response_model=BasePOSTResponse[AccessTokenResponseSchema],
    status_code=200,
    responses={
        403: {"model": BaseErrorResponse, "description" : "Token was invalid or expired"},
    },
    tags=["auth"],
)
def get_access_token(
    refresh_token: Annotated[
        str,
        Query(
            example="totally_valid_refresh_token",
            description="Refresh token obtained from a successful login",
        ),
    ],
):

    try:

        try:
            decoded_refresh_token = verify_jwt_throws(refresh_token)
        except jwt.ExpiredSignatureError:
            print("[DEBUG] Refresh Token expired")
            raise HTTPException(status_code=403, detail=f'Refresh token was expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=403, detail=f'Refresh token was invalid')
        
        # Currently for debugging purposes access tokens only last for 30 seconds
        new_access_token = generate_jwt(token_lifetime=timedelta(minutes=5), **decoded_refresh_token)

        payload_contents = AccessTokenResponseSchema(
            access_token=new_access_token,
        )
        
        return {
            'payload': payload_contents,
        }
        
    # Catching this in the generic block will result in the HTTPException being wrapped in an extra layer of HTTPException
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post(
    '/workouts/create',
    # TODO -> Make this BasePOSTResponse[WorkoutResponseSchema]
    response_model=BaseErrorResponse,
    status_code=201,
    responses={
        401: {"model": BaseErrorResponse, "description" : "There were authorization issues"},
        404: {"model": BaseErrorResponse, "description" : "Exercise requested doesn't exist"},
    },
    tags=["workouts"],
)
def create_workout(
    payload: CreateWorkoutSchema,
    db_session: Session = Depends(get_db),
    decoded_access_token: str = Depends(requires_authorization),
):

    return create_workout_raw(payload=payload, db_session=db_session, decoded_access_token=decoded_access_token)

@app.post(
    '/workouts/recommendation',
    response_model=BasePOSTResponse[WorkoutRecommendationResponseSchema],
    status_code=201,
    responses={
        401: {"model": BaseErrorResponse, "description" : "There were authorization issues"},
        404: {"model": BaseErrorResponse, "description" : "Exercise requested doesn't exist"},
    },
    tags=["workouts"],
)
def create_workout_recommendation(
    payload: WorkoutRecommendationRequestSchema,
    db_session: Session = Depends(get_db),
    decoded_access_token: str = Depends(requires_authorization),
):

    try:

        print("Running the route...")

        # Use real user ID
        ai_message = simple_prompt(
            user_query=payload.recommendation_request,
            user_id=decoded_access_token["user_id"],
        )

    except exc.IntegrityError as e:
        raise handle_integrity_errors(e)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    payload = WorkoutRecommendationResponseSchema(
        ai_message=ai_message,
    )

    return {'payload': payload}

@app.get(
    '/workouts/saved',
    response_model=BasePOSTResponse[SavedWorkoutsResponseSchema],
    responses={
        401: {"model": BaseErrorResponse, "description" : "There were authorization issues"},
    },
    status_code=200,
    tags=["workouts"],
)
def get_workouts(
    db_session: Session = Depends(get_db),
    decoded_access_token: str = Depends(requires_authorization),
):

    try:

        print("Running the route...")

        user_id = decoded_access_token["user_id"]
        print("[I] UserID:", user_id)

        workouts = get_workouts_for_user(
            db_session=db_session,
            user_id=user_id,
        )
        # print(json.dumps(workouts, indent=4))
        # Sort of pointless call, but at reminds that this schema is followed.

        # TODO -> Response schema isn't the final response schema at the moment
        payload = workouts

        payload = {
            "workouts" : payload,
        }

    except exc.IntegrityError as e:
        raise handle_integrity_errors(e)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {'payload': payload}

@app.post(
    '/workouts/update/components',
    # TODO -> Make this BasePOSTResponse[WorkoutUpdateResponseSchema]
    response_model=BaseErrorResponse,
    status_code=200,
    responses={
        401: {"model": BaseErrorResponse, "description" : "There were authorization issues"},
    },
    tags=["workouts"],
)
def update_workout(
    # TODO -> Use UpdateComponentsSchema
    payload: list[RetrievedWorkoutComponentSchema],
    db_session: Session = Depends(get_db),
    decoded_access_token: str = Depends(requires_authorization),
):

    # TODO -> Validate the user is the user these components are associated with

    # DONE -> Add a new version of all the components in the history table

    try:

        print("payload:", payload)

        db_session.add_all(
            map(
                lambda w_c: WorkoutComponentHistory(
                    workout_component_id=w_c.workout_component_id,
                    reps=w_c.reps,
                    weight=w_c.weight,
                    units=w_c.units,
                ),
                payload,
            ),
        )
        db_session.commit()

    except exc.IntegrityError as e:
        raise handle_integrity_errors(e)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Update complete"}

@app.post(
    '/workouts/finish',
    response_model=BaseErrorResponse,
    status_code=201,
    responses={
        401: {"model": BaseErrorResponse, "description" : "There were authorization issues"},
    },
    tags=["workouts"],
)
def finish_workout(
    # TODO -> Use FinishWorkoutSchema
    payload: list[RetrievedWorkoutComponentSchema],
    db_session: Session = Depends(get_db),
    decoded_access_token: str = Depends(requires_authorization),
):

    # TODO -> Validate the user is the user these components are associated with

    # TODO -> Sanity check that the workout components are from the same workout? Might be fine/better to decouple this though

    try:

        new_finished_workout_row = FinishedWorkouts()
        (
            db_session
            .add(
                new_finished_workout_row
            )
        )

        # No commit, so will rollback if anything fails later on in this sequence of DB operations
        db_session.flush()

        finished_workout_id = new_finished_workout_row.finished_workout_id

        db_session.add_all(
            map(
                lambda w_c: FinishedWorkoutComponents(
                    finished_workout_id=finished_workout_id,
                    workout_component_id=w_c.workout_component_id,
                ),
                payload,
            ),
        )
        db_session.commit()

    except exc.IntegrityError as e:
        raise handle_integrity_errors(e)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.rollback()

    # TODO -> Could in future return some stats for the app to show, like number of workouts completed this month, how long the workout took, ect.
    return {"message": "Workout Finished"}