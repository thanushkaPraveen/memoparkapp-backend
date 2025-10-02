from app.database.connection import Database


def user_types(db):
    user_types = UserType.select(db)

    if len(user_types) < 2:
        # Create a UserType object
        new_user_type = UserType(user_type="Admin", is_active=1)
        UserType.insert(db, new_user_type)

        # Create a UserType object
        new_user_type = UserType(user_type="User", is_active=1)
        UserType.insert(db, new_user_type)


def insert_records():
    # Create a Database object
    db = Database()