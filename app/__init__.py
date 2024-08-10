from fastapi import FastAPI

# Can also just be done in the top of the routes file
app = FastAPI(
    title="Workout App API",
    description="Request predictions from AI models",
    version="0.0.1",
    # contact=,
)

# TODO -> Setup and configure the base logger here

# Registers all the routes to the app object, as that code is now executed
from app import routes