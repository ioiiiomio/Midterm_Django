from decouple import Csv, config


ENV_ID = config("CAMPUS_ENV_ID", cast=str)
SECRET_KEY = config("CAMPUS_SECRET_KEY", cast=str)
ALLOWED_HOSTS = config("CAMPUS_ALLOWED_HOSTS", cast=Csv(), default="")

# for database postgreSQL
DB_NAME = config("CAMPUS_DB_NAME", cast=str, default="")
DB_USER = config("CAMPUS_DB_USER", cast=str, default="")
DB_PASSWORD = config("CAMPUS_DB_PASSWORD", cast=str, default="")
DB_HOST = config("CAMPUS_DB_HOST", cast=str, default="localhost")
DB_PORT = config("CAMPUS_DB_PORT", cast=int, default="5432")
