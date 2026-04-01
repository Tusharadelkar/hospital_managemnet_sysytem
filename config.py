import os

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "user":     os.getenv("DB_USER",     "TusharAdelkar"),
    "password": os.getenv("DB_PASSWORD", "SUNshine21#"),
    "database": os.getenv("DB_NAME",     "hospital_db"),
}
