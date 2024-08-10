from ..models import Users, Actions, ActionLog
from sqlalchemy.orm import Session

UNKNOWN_ACTION = "UNKNOWN_ACTION"
FAILED_LOG = "FAILED_LOG"

# ATTEMPT_LOGIN = "ATTEMPT_LOGIN" # Hard to track as user_id is required
SUCCESSFUL_LOG_IN = "SUCCESSFUL_LOG_IN"
UNSUCCESSFUL_LOG_IN = "UNSUCCESSFUL_LOG_IN"
LOGGED_OUT = "LOGGED_OUT"

def generate_actions_table(
    db_session: Session,
):

    actions = [
        SUCCESSFUL_LOG_IN,
        UNSUCCESSFUL_LOG_IN,
        LOGGED_OUT,

        UNKNOWN_ACTION,
        FAILED_LOG,
    ]

    action_rows = list(
        map(
            lambda action: Actions(action_name=action),
            actions,
        ),
    )

    db_session.add_all(action_rows)
    db_session.commit()

def log_action(
    action_name,
    db_session: Session,
    user_id=None,
    username=None,
) -> bool:
    """
    If both user_id and username are non-None, user_id is used.

    To avoid unneeded 500 codes, logging will fail silently if any exceptions or problems occur.
    """

    # TODO - Refactor, my goodness
    
    try:

        print(f"[LOGGING] Log request for {action_name}")

        if (not user_id is None) and ((not username is None)):
            raise ValueError("One of user_id or username should be non-None")
        
        if user_id is None:
            query = db_session.query(Users.user_id, Users.username).filter(Users.username == username)
            if query.count() != 1:
                print("[WARNING] Failed to log action due to being unable to find the correct user_id")
                return False

            user_id = query.first().user_id

        query = db_session.query(Actions.action_id, Actions.action_name).filter(Actions.action_name == action_name)
        if query.count() != 1:
            # Getting the action ID for an unknown action
            query = db_session.query(Actions.action_id, Actions.action_name).filter(Actions.action_name == UNKNOWN_ACTION)
        action_id = query.first().action_id

        action_log = ActionLog(
            user_id=user_id,
            action_id=action_id,
        )

        db_session.add(action_log)
        db_session.commit()
        
        return True

    except Exception as e:
        # Allowing execution to continue even though logging failed.
        print("[WARNING] Failed to log action due to an exception")
        print(e)
        return False