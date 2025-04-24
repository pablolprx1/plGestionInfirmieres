import mysql.connector
from mysql.connector import pooling

# Paramètres de connexion à la base de données
DATABASE_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'appplginfirmieres',
    'raise_on_warnings': True
}

# Pool de connexion pour la base de données
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mon_pool",
    pool_size=5,
    **DATABASE_CONFIG
)

def get_db():
    """Obtenir une connexion à partir du pool."""
    return connection_pool.get_connection()
