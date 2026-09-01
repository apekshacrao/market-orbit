class AuthService:
    @staticmethod
    def register(user_in):
        # Starter registration stub
        return {"id": "user-1", "email": user_in.email, "name": user_in.name, "is_active": True}

    @staticmethod
    def authenticate(login_data):
        # Starter auth stub
        return {"access_token": "mock_token", "token_type": "bearer"}
