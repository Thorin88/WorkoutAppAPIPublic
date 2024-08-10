from functools import wraps

from fastapi import HTTPException, Depends, Request

import jwt
from datetime import datetime, timedelta

from .secrets import get_secret

# https://stackoverflow.com/questions/64146591/custom-authentication-for-fastapi

def get_bearer_token_from_request(req: Request):
    """
    Needs to be called in a context where request is available, such as an endpoint.
    """
    authorization_header = "Authorization"
    authorization_header = req.headers.get(authorization_header, None)

    if not authorization_header:
        raise HTTPException(
            status_code=401,
            detail="No authorization header found in the request.",
        )

    authorization_header_elements = authorization_header.split()

    if len(authorization_header_elements) != 2:
        raise HTTPException(
            status_code=401,
            detail="Authorization header formatting was invalid.",
        )

    auth_scheme = authorization_header_elements[0]
    bearer_token = authorization_header_elements[1]

    expected_auth_scheme = "bearer"

    if not (auth_scheme and auth_scheme.lower() == expected_auth_scheme):
        raise HTTPException(
            status_code=401,
            detail=f"Authorization header was expected to use the following scheme: {expected_auth_scheme}.",
        )

    if not bearer_token:
        raise HTTPException(
            status_code=401,
            detail="Could not find the required information in the authorization header.",
        )
    
    return bearer_token
    
def requires_authorization(req: Request):

    access_token = get_bearer_token_from_request(req)
    # ???
    # if (isinstance(access_token, tuple)):
    #     print(access_token)
    #     return access_token

    print(f"[requires_authorization] Token: {access_token}")

    # Validate Token
    try:
        # TODO -> Pass access token to the caller
        decoded_access_token = verify_jwt_throws(access_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=f'Endpoint requires authorization: Access token was expired',
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail=f'Endpoint requires authorization: Access token was invalid',
        )

    return decoded_access_token

# def requires_authorization(function):
#     @wraps(function)
#     def decorator(*args, **kwargs):
#         access_token = get_bearer_token_from_request()
#         if (isinstance(access_token, tuple)):
#             print(access_token)
#             return access_token

#         print(f"[requires_authorization] Token: {access_token}")

#         # Validate Token
#         try:
#             # TODO -> Pass access token to the caller
#             decoded_access_token = verify_jwt_throws(access_token)
#         except jwt.ExpiredSignatureError:
#             return {'message': f'Endpoint requires authorization: Access token was expired'}, 401
#         except jwt.InvalidTokenError:
#             return {'message': f'Endpoint requires authorization: Access token was invalid'}, 401

#         return function(*args, **kwargs, decoded_access_token=decoded_access_token)

#     return decorator

# TODO -> This is a demo app, but eventually this will be a GCP secret
jwt_secret_key = get_secret("workout-app-api-jwt-key")

# TODO -> Should probably make the JWT contents explicit params so it is clear what goes in them,
# as at the momement the contents are defined in the login functions.
def generate_jwt(token_lifetime=timedelta(minutes=30),**token_contents):
    """
    Creates a JWT containing the key-value (parameter_name-value) pairs that are provided as argument to this function.
    The token also contains an expiry time that is determinded based on the token_life_time parameter.
    :param token_contents: Dict. The parameters provided to this function.
    :param token_lifetime: timedelta. An object representing how long much time to add to the current time in order to form
    the token's expiry time.
    :return: str. The JWT token generated
    """
    # TODO -> Use token contents
    payload = token_contents
    # UTC to ensure a commonly used timezone
    payload['exp'] = datetime.utcnow() + token_lifetime

    print("[DEBUG] Token contents:", payload)

    # TODO -> Have a real secret key
    # Secret key (used to sign the token)
    secret_key = jwt_secret_key

    # Generate the JWT
    token = jwt.encode(payload, secret_key, algorithm='HS256')

    return token

def verify_jwt(token):
    """
    Will check if:
    1. Verify signature of the token (came from this API and not been tampered with)
    2. The token is in-date
    3. Extract the info from the token
    :param token: str. The JWT token to check
    :return:
    """
    try:
        # Verify the token using the secret key
        decoded_token = jwt.decode(token, jwt_secret_key, algorithms=['HS256'])

        # The token is valid if decoding doesn't raise an exception
        print("[DEBUG] Token is valid!")
        print(type(decoded_token))
        print(decoded_token)  # The decoded token claims

        return True, decoded_token

    except jwt.ExpiredSignatureError:
        print("[DEBUG] Token has expired!")
        return False, None
    except jwt.InvalidTokenError:
        print("[DEBUG] Token is invalid!")
        return False, None
    
def verify_jwt_throws(token):
    """
    Will check if:
    1. Verify signature of the token (came from this API and not been tampered with)
    2. The token is in-date
    3. Extract the info from the token
    :param token: str. The JWT token to check
    :return:
    :throws: jwt.ExpiredSignatureError if the token has expired
    :throws: jwt.InvalidTokenError if the token was invalid
    """
    # Verify the token using the secret key
    decoded_token = jwt.decode(token, jwt_secret_key, algorithms=['HS256'])

    # The token is valid if decoding doesn't raise an exception
    print("[DEBUG] Token is valid!")
    print(type(decoded_token))
    print(decoded_token)  # The decoded token claims

    return decoded_token

# def get_jwt_contents -> TODO