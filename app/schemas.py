from pydantic import BaseModel, Field, validator
from typing import Generic, TypeVar

# TODO -> Make base model with extra = "forbid"

PayloadType = TypeVar('PayloadType')

class BasePOSTResponse(BaseModel, Generic[PayloadType]):

    payload: PayloadType

    class Config:
        extra = "forbid"

class BaseErrorResponse(BaseModel):

    message : str

    class Config:
        extra = "forbid"

class NewUserSchema(BaseModel):

    username : str = Field(description="Desired username")
    hash : str = Field(description="The hash of their password and the provided salt")
    salt : str = Field(description="The salt used to generate the hash")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "username" : "Thorin",
                    "hash" : "crashout",
                    "salt" : "NaOH",
                }
            ]
        }

# Used Query and Annotation instead of this model: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# class SaltRequestSchema(BaseModel):

#     username : str = Field(description="Username to get the salt for, where this salt was used to generate their original password hash", example="Thorin")

#     class Config:
#         extra = "forbid"

class SaltResponseSchema(BaseModel):

    salt : str = Field(description="The salt used to generate a user's original password hash")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "salt" : "NaOH",
                }
            ]
        }

class LoginRequestSchema(BaseModel):

    username : str = Field(description="Username to log in with")
    hash : str = Field(description="Hash of the entered password and their original salt")

    class Config:
        extra = "forbid"

class LoginResponseSchema(BaseModel):

    refresh_token : str = Field(description="A signed JWT token that can be used to request access tokens")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "refresh_token" : "totally_valid_token",
                }
            ]
        }

# TODO -> Return a better payload
class CreateWorkoutResponseSchema(BaseModel):

    message : str = Field(description="Associated message")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "message" : "Workout created",
                }
            ]
        }
    
# class AccessTokenRequestSchema(BaseModel):

#     refresh_token : str = Field(description="Refresh token that was sent upon successful login")

#     class Config:
#         extra = "forbid"

class AccessTokenResponseSchema(BaseModel):

    access_token : str = Field(description="An access token for the user associated with the provided refresh token")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "access_token" : "totally_valid_access_token",
                }
            ]
        }
        
class BaseWorkoutComponentSchema(BaseModel):

    exercise_name : str = Field(description="Name of an exercise known to the API")

    # TODO -> Check >= 0
    position : int = Field(description="Position of this workout component in the workout")
    reps : str = Field(description="A string representing the rep range for the workout component")
    weight : float = Field(description="The weight to use for this exercise, without units")
    # TODO -> Check the units
    units : str = Field(description="Units for the weight")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "exercise_name" : "bicep_curls",
                    "position" : 0,
                    "reps" : "6-8",
                    "weight" : 20.0,
                    "units" : "kg",
                }
            ]
        }

class RetrievedWorkoutComponentSchema(BaseWorkoutComponentSchema):

    workout_component_id : str = Field(description="The workout component's UUID")

    class Config:
        extra = "forbid"

class WorkoutRecommendationRequestSchema(BaseModel):

    recommendation_request : str = Field(description="A description of the workout to be recommended")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "examples" : [
                {
                    "recommendation_request" : "A workout for my chcst, with 2 or 3 exercises please",
                }
            ]
        }

class WorkoutRecommendationResponseSchema(BaseModel):

    ai_message : str = Field(description="The LLM's response")

    class Config:
        extra = "forbid"

class CreateWorkoutSchema(BaseModel):

    name : str = Field(description="Name of the workout")
    ai_generated : bool = Field(description="Whether the workout was generated by AI or not")
    workout_components : list[BaseWorkoutComponentSchema] = Field(description="List of workout components in the workout")

    class Config:
        extra = "forbid"

class RetrievedWorkoutSchema(BaseModel):

    name : str = Field(description="Name of the workout")
    ai_generated : bool = Field(description="Whether the workout was generated by AI or not")
    workout_components : list[RetrievedWorkoutComponentSchema] = Field(description="List of workout components in the workout")

    class Config:
        extra = "forbid"

class SavedWorkoutsResponseSchema(BaseModel):

    workouts : list[RetrievedWorkoutSchema] = Field(description="List of workouts retrieved")

    class Config:
        extra = "forbid"

# Currently unused
class UpdateComponentsSchema(BaseModel):

    workout_components : list[RetrievedWorkoutComponentSchema] = Field(description="List of updated workout components in the workout")

    class Config:
        extra = "forbid"

class FinishWorkoutSchema(BaseModel):

    workout_components : list[RetrievedWorkoutComponentSchema] = Field(description="List of completed workout components")

    class Config:
        extra = "forbid"