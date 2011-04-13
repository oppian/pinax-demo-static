"""
Settings file to use in deployments. Is a template that will have it's values filled in by build server.
"""
DEBUG = $DEBUG
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    "default": {
        "ENGINE": "postgresql_psycopg2",
        "NAME": '$DB_NAME',
        "USER": '$DB_USER',
        "PASSWORD": '$DB_PASS',
        "HOST": '$DB_HOST',
        "PORT": "",
    }
}

ADMINS = (
    ('Stephen Hartley', 'steve@oppian.com'),
    ('Matthew Jacobi', 'matt@oppian.com'),
)

# Default admin account and pass

MANAGERS = ADMINS

SITE_DOMAIN = "$SITE_DOMAIN"