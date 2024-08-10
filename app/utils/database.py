from sqlalchemy import cast, Text, select
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import aliased, Session

from fastapi import HTTPException

from .custom_exceptions import ExerciseDoesNotExistException, UsernameAlreadyExistsException, UsernameDoesNotExistException
from .logging import generate_actions_table

from ..models import (
    Users, UserPasswordHashes, Actions, ActionLog,
    Exercises, UserWorkouts, WorkoutComponents,
    WorkoutComponentHistory, FinishedWorkoutComponents, FinishedWorkouts,
)

import re
import pandas as pd
import json

from typing import List

# https://docs.sqlalchemy.org/en/14/orm/query.html

# TODO: Make into a generic DB error handling function
def handle_integrity_errors(e):
    """
    Parses the exception message to try and extract some useful information, specifically
    regarding integrity errors.
    :param e: Exception. The exception to check.
    :return: Tuple(Dict, int). A response (JSON) and a HTTP status code.
    """
    err_msg = str(e)
    status_code = 500
    regex = ".*Key \((.*)\)=\((.*)\) already exists.*" # Note that the non-escaped brackets specify the parts of this match to return
    re_match = re.search(regex, err_msg)
    if re_match is not None:
        err_msg = f"Insertion failed. The value for {re_match.group(1)} [{re_match.group(2)}] already exists in the DB."
        status_code = 409
    return HTTPException(status_code=status_code, detail=str(err_msg))

def generic_add_to_table(table_class, json_payload, return_attribute=None):
    """
    Attempts to use the provided json payload to construct an instance of a table row, and
    then add this row to the table in the database. Designed for tables which are able to
    ignore any unneeded parameters, or if the json payload has already been trimmed down to
    only the required fields.
    :param table_class: db.Model. The class of the table to insert into.
    :param json_payload: Dict. The JSON payload containing an entity that can be inserted into
    this table.
    :param return_attribute: str. The attribute of the newly inserted row to return.
    :return: Any. The value of the specified attribute of the newly inserted row, or None if attribute not present fails.
    """

    new_row = table_class(**json_payload)
    db.session.add(new_row)
    db.session.commit()

    if return_attribute is None:
        return

    returned_attribute = getattr(new_row, return_attribute, None)
    if returned_attribute is None:
        print("[W] generic_add_to_table: Unable to find specified return_attribute")
        db.session.delete(new_row)
        db.session.commit()

    return returned_attribute

# Throws UsernameAlreadyExistsException and standard SQL related exceptions
def attempt_insert_new_user(
    json_payload,
    db_session,
    user_table_class=Users,
    password_table_class=UserPasswordHashes,
):

    new_row = user_table_class(
        username=json_payload.username,
    )
    query = db_session.query(user_table_class.username).filter(user_table_class.username == new_row.username)
    results = query.all()
    if len(results) > 0:
        raise UsernameAlreadyExistsException()
    
    db_session.add(new_row)
    db_session.commit()

    assigned_user_id = new_row.user_id

    new_row = password_table_class(
        user_id=assigned_user_id,
        hash=json_payload.hash,
        salt=json_payload.salt,
    )

    db_session.add(new_row)
    db_session.commit()

    return assigned_user_id

def login_user(
    json_payload,
    db_session: Session,
    user_table_class=Users,
    password_table_class=UserPasswordHashes,
):
    
    username_to_login = json_payload.username
    # Use joins, to avoid a cartesian join
    query = (
        db_session
        .query(user_table_class, password_table_class)
        .filter(user_table_class.user_id == password_table_class.user_id)
        .filter(user_table_class.username == username_to_login)
    )
    results = query.all()

    if len(results) == 0:
        raise UsernameDoesNotExistException()
    elif len(results) > 1:
        raise Exception(f"Multiple users in database with this username (shouldn't happen): [{username_to_login}]")
    
    # TODO -> Make this access more safe
    stored_hash = results[0][1].hash
    user_id = results[0][1].user_id

    useful_user_info = {
        "user_id": str(user_id), # Needs str() as json decoder does not handle this itself
        "username": username_to_login,
    }

    is_correct_password = stored_hash == json_payload.hash

    # Sanity check, don't return the user_id if the password was wrong.
    if not is_correct_password:
        useful_user_info = None

    return is_correct_password, useful_user_info

def generate_exercises_table(
    db_session: Session,
):

    exercises = [
        {
            "exercise_name" : "flat_dumbell_press",
        },
        {
            "exercise_name" : "incline_dumbell_press",
        },
        {
            "exercise_name" : "forward_dumbell_raises",
        },
        {
            "exercise_name" : "shrugs",
        },
        {
            "exercise_name" : "dumbell_row",
        },
        {
            "exercise_name" : "lateral_raises",
        },
        {
            "exercise_name" : "lat_pull_downs",
        },
        {
            "exercise_name" : "tricep_pulldowns",
        },
        {
            "exercise_name" : "chest_fly",
        },
        {
            "exercise_name" : "reverse_chest_fly",
        },
        {
            "exercise_name" : "seated_rows",
        },
        {
            "exercise_name" : "bicep_curls",
        },
        {
            "exercise_name" : "squats",
        },
        {
            "exercise_name" : "pistol_squats",
        },
        {
            "exercise_name" : "romanian_deadlifts",
        },
        {
            "exercise_name" : "leg_press",
        },
        {
            "exercise_name" : "lunges",
        },
        {
            "exercise_name" : "leg_curls",
        },
        {
            "exercise_name" : "leg_extensions",
        },
        {
            "exercise_name" : "dips",
        },
        {
            "exercise_name" : "push_ups",
        },
    ]

    exercise_rows = list(
        map(
            lambda exercise: Exercises(**exercise),
            exercises,
        ),
    )

    db_session.add_all(exercise_rows)
    db_session.commit()

def insert_user_workout_identifier(
    db_session: Session,
    user_id,
    workout_name,
    ai_generated=False,
):
    
    user_workout = UserWorkouts(
        user_id=user_id,
        workout_name=workout_name,
        ai_generated=ai_generated,
    )

    db_session.add(user_workout)
    db_session.commit()

    return user_workout.workout_id

def insert_workout_component(
    db_session: Session,
    workout_id,
    exercise_id,
    position,
    reps,
    weight,
    units,
):
    
    workout_component = WorkoutComponents(
        workout_id,
        exercise_id,
        position,
    )
    db_session.add(workout_component)
    db_session.commit()
    # Have to commit to get the ID
    workout_component_id = workout_component.workout_component_id

    first_workout_component_history = WorkoutComponentHistory(
        workout_component_id,
        reps,
        weight,
        units,
    )

    db_session.add(first_workout_component_history)
    db_session.commit()

    return workout_component.workout_component_id

def insert_workout_component_from_name(
    db_session: Session,
    exercise_name,
    workout_id,
    position,
    reps,
    weight,
    units,
):
    
    print(f"[DEBUG] Looking for exercise ID...")
    
    query = (
        db_session
        .query(Exercises.exercise_id)
        .filter(Exercises.exercise_name == exercise_name)
    )
    # Basically checking if count == 0, as excercise_name is unique
    if query.count() != 1:
        raise ExerciseDoesNotExistException(name=exercise_name)
    
    exercise_id = query.first().exercise_id

    print(f"[DEBUG] Ready to insert named exercise using ID {exercise_id}")

    return insert_workout_component(
        db_session=db_session,
        workout_id=workout_id,
        exercise_id=exercise_id,
        position=position,
        reps=reps,
        weight=weight,
        units=units,
    )

# There are a series of commits here. Can either have them all triggering, or have none of them trigger
# and leave it up to the caller to commit the data. How do commits work in the sense of IDs being taken up and
# the implications of multiple writes happening. Perhaps transactions are independant so can be rolled back easily.
def create_new_workout(
    db_session: Session,
    user_id,
    workout_name,
    workout_components, # Deserialized via WorkoutComponentSchema 
    ai_generated=False,
):

    print("[DEBUG] Creating Workout Identifier")

    workout_id = insert_user_workout_identifier(
        db_session=db_session,
        user_id=user_id,
        workout_name=workout_name,
        ai_generated=ai_generated,
    )

    print("[DEBUG] Created Workout Identifier")
    
    for workout_component in workout_components:
        insert_workout_component_from_name(
            db_session=db_session,
            workout_id=workout_id,
            exercise_name=workout_component.exercise_name,
            position=workout_component.position,
            reps=workout_component.reps,
            weight=workout_component.weight,
            units=workout_component.units,
        )

    return workout_id

def populate_base_tables(db_session: Session):

    generate_actions_table(db_session=db_session)
    print("[DEBUG] Actions table populated")
    generate_exercises_table(db_session=db_session)
    print("[DEBUG] Exercise table populated")

def get_known_workout_names(
    db_session: Session,
) -> List[str]:

    exercise_rows_from_db = (
        db_session
        .query(Exercises.exercise_name)
        .all()
    )

    known_exercise_names = list(
        map(
            lambda row_obj: row_obj.exercise_name,
            exercise_rows_from_db,
        )
    )

    return known_exercise_names

# select * from
# user_workouts uw inner join workout_components wc on uw.workout_id = wc.workout_id
# inner join exercises e on wc.exercise_id = e.exercise_id 
# and user_id = 'c45ee2df-c8b8-4a78-86f9-b0a8ff510b8f'
def get_workouts_for_user(
    db_session : Session,
    user_id,
):
    
    workouts = []

    # Safer to build result from returned Workout IDs and then querying
    # each one sequentially, since transaction wise it's safer to do one big read and then format
    # the results.

    # Work out, for each component_id, it's latest version. We will use this to only
    # extract workout components + histories for this most recent version of the component.
    max_date_sub_query = (
        db_session
        .query(
            WorkoutComponentHistory.workout_component_id,
            func.max(WorkoutComponentHistory.datetime_added).label('max_datetime_added'),
        )
        .group_by(WorkoutComponentHistory.workout_component_id)
        .subquery()
    )

    # Due to the nature of group by, we cannot select the history_id in the above sub query. Hence we can
    # get the set of the latest component histories ID for all components using another sub query.
    sub_query = (
        db_session
        .query(
            WorkoutComponentHistory.workout_component_history_id,
        )
        .where(
            (max_date_sub_query.c.max_datetime_added == WorkoutComponentHistory.datetime_added)
            & (max_date_sub_query.c.workout_component_id == WorkoutComponentHistory.workout_component_id)
        )
        .subquery()
    )

    query = (
        db_session
        .query(
            UserWorkouts.workout_id,
            UserWorkouts.datetime_created,
            UserWorkouts.workout_name,
            UserWorkouts.ai_generated,
            Exercises.exercise_name,
            WorkoutComponents.workout_component_id,
            WorkoutComponents.position,
            WorkoutComponentHistory.reps,
            WorkoutComponentHistory.weight,
            WorkoutComponentHistory.units,
            WorkoutComponentHistory.datetime_added,
        )
        .select_from(UserWorkouts)
        .join(WorkoutComponents, UserWorkouts.workout_id == WorkoutComponents.workout_id)
        .join(WorkoutComponentHistory, WorkoutComponents.workout_component_id == WorkoutComponentHistory.workout_component_id)
        .join(Exercises, WorkoutComponents.exercise_id == Exercises.exercise_id)
        .join(sub_query, sub_query.c.workout_component_history_id == WorkoutComponentHistory.workout_component_history_id)
        .filter(UserWorkouts.user_id == user_id)
        .order_by(UserWorkouts.datetime_created, UserWorkouts.workout_id, WorkoutComponents.position)
    )

    if query.count() <= 0:
        return workouts
    
    # print(query.statement)

    query_result = query.all()
    query_result_df = pd.DataFrame(query_result)

    workouts = []

    # Formating the query results into the form that the relevant GET endpoint is promising to return
    for i, workout_id in enumerate(query_result_df.workout_id.unique()):
        workout_splice = query_result_df.workout_id == workout_id
        workout_df = query_result_df[workout_splice]
        # TODO - There is surely a cleaner way to get this name
        workout_name = workout_df.workout_name.iloc[0]
        workout_is_ai_generated = workout_df.ai_generated.iloc[0]
        workout_df = query_result_df[workout_splice].drop(
            columns=[
                "workout_id",
                "workout_name",
                "ai_generated",
                "datetime_created",
                "datetime_added",
            ],
        )
        workout_df["workout_component_id"] = workout_df["workout_component_id"].apply(str)

        workout_as_dict = workout_df.to_dict(orient="records")
        workout_to_add = {
            # TODO -> Use name from DB
            "name" : workout_name,
            "ai_generated" : workout_is_ai_generated,
            "workout_components" : workout_as_dict,
        }

        workouts.append(workout_to_add)

    # print(json.dumps(workouts, indent=4))

    return workouts

def get_latest_finished_workouts_for_user(
    db_session : Session,
    user_id,
):
    """
    Only used by the LLMs, does not return the same things as intended for a typical use case of this type of function
    """
    
    workouts = []

    # Safer to build result from returned Workout IDs and then querying
    # each one sequentially, since transaction wise it's safer to do one big read and then format
    # the results.

    # Work out, for each component_id, it's latest version. We will use this to only
    # extract workout components + histories for this most recent version of the component.
    max_date_sub_query = (
        db_session
        .query(
            WorkoutComponentHistory.workout_component_id,
            func.max(WorkoutComponentHistory.datetime_added).label('max_datetime_added'),
        )
        .group_by(WorkoutComponentHistory.workout_component_id)
        .subquery()
    )

    # Due to the nature of group by, we cannot select the history_id in the above sub query. Hence we can
    # get the set of the latest component histories ID for all components using another sub query.
    sub_query = (
        db_session
        .query(
            WorkoutComponentHistory.workout_component_history_id,
        )
        .where(
            (max_date_sub_query.c.max_datetime_added == WorkoutComponentHistory.datetime_added)
            & (max_date_sub_query.c.workout_component_id == WorkoutComponentHistory.workout_component_id)
        )
        .subquery()
    )

    query = (
        db_session
        .query(
            UserWorkouts.workout_id,
            UserWorkouts.datetime_created,
            UserWorkouts.workout_name,
            Exercises.exercise_name,
            WorkoutComponents.workout_component_id,
            WorkoutComponents.position,
            WorkoutComponentHistory.reps,
            WorkoutComponentHistory.weight,
            WorkoutComponentHistory.units,
            WorkoutComponentHistory.datetime_added,
        )
        .select_from(UserWorkouts)
        .join(WorkoutComponents, UserWorkouts.workout_id == WorkoutComponents.workout_id)
        .join(WorkoutComponentHistory, WorkoutComponents.workout_component_id == WorkoutComponentHistory.workout_component_id)
        .join(Exercises, WorkoutComponents.exercise_id == Exercises.exercise_id)
        # Join to the latest version of the workout component
        .join(sub_query, sub_query.c.workout_component_history_id == WorkoutComponentHistory.workout_component_history_id)
        .join(FinishedWorkoutComponents, FinishedWorkoutComponents.workout_component_id == WorkoutComponents.workout_component_id)
        .join(FinishedWorkouts, FinishedWorkouts.finished_workout_id == FinishedWorkoutComponents.finished_workout_id)
        .filter(UserWorkouts.user_id == user_id)
        .order_by(FinishedWorkouts.completed_datetime.desc(), UserWorkouts.workout_id, WorkoutComponents.position)
        .limit(5)
    )

    if query.count() <= 0:
        return workouts
    
    # print(query.statement)

    query_result = query.all()
    query_result_df = pd.DataFrame(query_result)

    workouts = []

    # Formating the query results into the form that the relevant GET endpoint is promising to return
    for i, workout_id in enumerate(query_result_df.workout_id.unique()):
        workout_splice = query_result_df.workout_id == workout_id
        workout_df = query_result_df[workout_splice]
        # TODO - There is surely a cleaner way to get this name
        workout_name = workout_df.workout_name.iloc[0]
        workout_df = query_result_df[workout_splice].drop(
            columns=[
                "workout_id",
                "workout_name",
                "datetime_created",
                "datetime_added",
            ],
        )
        workout_df["workout_component_id"] = workout_df["workout_component_id"].apply(str)

        workout_as_dict = workout_df.to_dict(orient="records")
        workout_to_add = {
            # TODO -> Use name from DB
            "name" : workout_name,
            # Does not include the AI generated field
            # "ai_generated" : workout_is_ai_generated,
            "workout_components" : workout_as_dict,
        }

        workouts.append(workout_to_add)

    # print(json.dumps(workouts, indent=4))

    return workouts
