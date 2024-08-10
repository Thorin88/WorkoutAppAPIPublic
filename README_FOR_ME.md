# Workout App API

## Documentation

Please run the API and visit the endpoint `readthedocs` in your browser. This page contains detailed information about the endpoints provided by this API.

## How it works

TODO

## Running the API

### Local

Environment variables for this configuration are to be defined in the `config/local.env` file.

1. Run `docker-compose up --build --remove-orphans`

This will setup up the API listening on the port specified via the environment variable `PORT`, and a Postgres database listening on the port specified via the environment variable `LOCAL_DB_PORT`.

## TODO

Use better endpoint types (eg PUT/POST for create_tables, DELETE for drop_tables)

Remove User ID from the returned message from the signup endpoint. This information is currently for debugging, but the device should not be
trying to get information from this response, as signup will always require then navigating to the login page

Better logging, using some kind of logging tool/API.

Use a proper secret key for JWT encyption

Add parameters to the comments on the GET endpoints

Make functions that use the generic jwt generation for refresh and access tokens

Is a refresh token supposed to be rejected when provided instead of an access token? At the moment, the refresh token would be accepted if it were passed in the
authorisation header. Could add a tag within the token to indicate that this token is an access or refresh token.

Pass valid refresh tokens to the endpoints that require them, if they need the info inside them.

Next step is adding a update option to components, and checking they update correctly via the query

### Adding Workout Names

~~Added to models~~

~~Added to insert workout~~

~~Added to create workout endpoint~~

~~Add to app API calls and models~~

~~AI recommendation needs to provide one~~

Could ask it to provide a consistent format, like capitalised

~~Added to recommendation endpoint~~

~~GET endpoint needs to use the name from the DB~~

Update doc example

### Swagger for testing

https://stackoverflow.com/questions/45199989/how-do-i-automatically-authorize-all-endpoints-with-swagger-ui

### App testing

https://developer.android.com/docs/quality-guidelines/core-app-quality

## Links

https://flask-marshmallow.readthedocs.io/en/latest/: Useful for examples of well laid out APIs

https://marshmallow.readthedocs.io/en/stable/quickstart.html: Useful examples of using schemas. Interesting set of options for serialisation with schemas.
They are just a bit fiddle to debug because they don't validate like when loading with a schema.

## Tips

This warning:
```
SAWarning: SELECT statement has a cartesian product between FROM element(s)
```
Means that a query was specified multiple tables, but not joined then in anyway, like with .id = .id. This shouldn't be ignored if spotted.

GET endpoints should never use a request body. Use query parameters.

Could look into using FastAPI? https://www.reddit.com/r/flask/comments/13pyxie/flask_vs_fastapi/

## Bugs

Workout Components returned by the API

### FastAPI

Instead of a global db object, a connection factor is injected into endpoint functions which require it.

Be careful when using custom exception handlers and catching generic exceptions. Such a block can catch HTTPExceptions that the code throws. This will result in the error being wrapped up in a new exception, and will mess up the error codes you would expect from the endpoint.