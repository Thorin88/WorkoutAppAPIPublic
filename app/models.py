from .database import Base

import uuid
from sqlalchemy import ForeignKey, func, Column, String, Integer, DateTime, Boolean, Float

from sqlalchemy.dialects.postgresql import UUID

# https://docs.sqlalchemy.org/en/20/core/type_basics.html

class Users(Base):

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    username = Column(String(30), unique=True, nullable=False)

    def __init__(self,
                 username,
                 **kwargs,
                 ):
        
        self.username = username

class UserPasswordHashes(Base):

    __tablename__ = "user_password_hashes"

    user_id = Column(UUID(as_uuid=True), ForeignKey(Users.user_id), primary_key=True)
    hash = Column(String(64), nullable=False)
    salt = Column(String(32), nullable=False)

    def __init__(self,
                 user_id,
                 hash,
                 salt,
                 **kwargs,
                 ):
        
        self.user_id = user_id
        self.hash = hash
        self.salt = salt

class Actions(Base):

    __tablename__ = "actions"

    action_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    action_name = Column(String(30), unique=True, nullable=False)

    def __init__(self,
                 action_name,
                 **kwargs,
                 ):
        
        self.action_name = action_name

class ActionLog(Base):

    __tablename__ = "action_log"

    """
    Not currently intended to be able to tell you if a user is logged in or not, since some uncontrolled actions
    can result in the user being logged out in the app. But does track loggin attempts.
    """

    log_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled

    user_id = Column(UUID(as_uuid=True), ForeignKey(Users.user_id))
    # Other useful fields could be added here as needed.

    action_id = Column(UUID(as_uuid=True), ForeignKey(Actions.action_id))
    action_datetime = Column(DateTime(timezone=False), server_default=func.current_timestamp(), nullable=False) # Auto filled

    def __init__(self,
                 user_id,
                 action_id,
                 **kwargs,
                 ):
        
        self.user_id = user_id
        self.action_id = action_id

class Exercises(Base):

    __tablename__ = "exercises"

    exercise_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    exercise_name = Column(String(30), unique=True, nullable=False)

    # TODO - Other info like image/icon, desc, tips, instructions

    def __init__(self,
                 exercise_name,
                 **kwargs,
                 ):
        
        self.exercise_name = exercise_name

class UserWorkouts(Base):

    __tablename__ = "user_workouts"

    workout_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    # TODO -> Link to workout metadata table?
    user_id = Column(UUID(as_uuid=True), ForeignKey(Users.user_id))
    workout_name = Column(String(100), unique=False, nullable=False)
    ai_generated = Column(Boolean, nullable=False)

    datetime_created = Column(DateTime(timezone=False), server_default=func.current_timestamp(), nullable=False) # Auto filled

    def __init__(self,
                 user_id,
                 workout_name,
                 ai_generated,
                 **kwargs,
                 ):
        
        self.user_id = user_id
        self.workout_name = workout_name
        self.ai_generated = ai_generated

# Entities that make up a workout
class WorkoutComponents(Base):

    __tablename__ = "workout_components"

    workout_component_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    workout_id = Column(UUID(as_uuid=True), ForeignKey(UserWorkouts.workout_id))
    exercise_id = Column(UUID(as_uuid=True), ForeignKey(Exercises.exercise_id))

    position = Column(Integer, nullable=False)

    def __init__(self,
                 workout_id,
                 exercise_id,
                 position,
                 **kwargs,
                 ):
        
        self.workout_id = workout_id
        self.exercise_id = exercise_id
        self.position = position

class WorkoutComponentHistory(Base):
    """
    Tracks changes to workout components.

    Note: If components are able to be added/removed from workouts in future, take note of how joins
    are being done for retrieval/analytics.
    """

    __tablename__ = "workout_component_history"

    workout_component_history_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True) # Auto filled
    workout_component_id = Column(UUID(as_uuid=True), ForeignKey(WorkoutComponents.workout_component_id), nullable=False)

    datetime_added = Column(DateTime(timezone=False), server_default=func.current_timestamp(), nullable=False) # Auto filled

    reps = Column(String(30), nullable=False) # Not an Int since could be a range
    weight = Column(Float, nullable=False)
    units = Column(String(30), nullable=False)

    def __init__(self,
                 workout_component_id,
                 reps,
                 weight,
                 units,
                 **kwargs,
                 ):
        
        self.workout_component_id = workout_component_id
        self.reps = reps
        self.weight = weight
        self.units = units

class FinishedWorkouts(Base):
    """
    Manages IDs of completed workouts
    """

    __tablename__ = "finished_workouts"

    # Essentially indicates which completed components are related (can't use workout ID, needs to be an ID for this specific completion instance)
    finished_workout_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    completed_datetime = Column(DateTime(timezone=False), server_default=func.current_timestamp(), nullable=False)

    def __init__(self):
        pass

class FinishedWorkoutComponents(Base):
    """
    Workout components which were completed in workouts
    """

    __tablename__ = "finished_workout_components"

    finished_workout_component_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    finished_workout_id = Column(UUID(as_uuid=True), ForeignKey(FinishedWorkouts.finished_workout_id), nullable=False)
    workout_component_id = Column(UUID(as_uuid=True), ForeignKey(WorkoutComponents.workout_component_id), nullable=False)

    def __init__(self,
                 finished_workout_id,
                 workout_component_id,
                 ):
        
        self.workout_component_id = workout_component_id
        self.finished_workout_id = finished_workout_id