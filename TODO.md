### Login Records

Without some sort of record of issued tokens, it is hard for the backend to force a user to have to login again.

### Logout

Once login records are decided, the API needs to provide an endpoint that can be used to log users out.

### Recommendation

Could eventually consider user's existing workouts, or most recent workout. Eg to get better weight suggestions

User could even be allowed to ask for edits before anything is saved to the database. Could then have a save button that prompt the LLM to call the final write.

Or the user could start from a prefilled AI recommended workout

### General

CRUD

Schema validation fields

BaseModel with desired config

Logging, start up in init file. Replace all prints. Log errors

Docker file copies whole source code, not just the app directory

Investigate how well FastAPI handles database connections, eg pools

Basic response model for endpoints which just return a message

Remove DB creation and deletion from the API, either as a script or via alembic

Use response models for all endpoints

Update docker

Use Depends(verify_token) for the tokens in authenticated URLs, no need for wrapper

Use a proper JWT secret key

Document error codes and response objects

Endpoint descriptions

Use async

Limit query param lengths

Limit AI prompt length

Endpoint status codes

### Issues

AI seems to put 0 as the weight a lot. Might be because the prompt leads it too.