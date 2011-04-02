"""
Settings file to use in deployments. Is a template that will have it's values filled in by build server.
"""
DEBUG = $DEBUG
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = '$DB_NAME'              # Or path to database file if using sqlite3.
DATABASE_USER = '$DB_USER'             # Not used with sqlite3.
DATABASE_PASSWORD = '$DB_PASS'         # Not used with sqlite3.
DATABASE_HOST = '$DB_HOST'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

ADMINS = (
    ('Stephen Hartley', 'steve@oppian.com'),
    ('Matthew Jacobi', 'matt@oppian.com'),
)

# Default admin account and pass

MANAGERS = ADMINS

SITE_DOMAIN = "$SITE_DOMAIN"