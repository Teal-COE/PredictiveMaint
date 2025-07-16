# PredictiveMaint



pip install mssql-django




DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'PM',  # Your local database name
        'USER': 'sa',  # Your SQL Server username
        'PASSWORD': 'admin@123',  # Your SQL Server password
        'HOST': 'localhost',  # Use 'localhost' or '127.0.0.1' for local DB
        'PORT': '1433',  # Default SQL Server port
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
        },
    }
}



python manage.py makemigrations
python manage.py migrate


