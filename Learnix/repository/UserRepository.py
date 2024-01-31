from sqlalchemy import create_engine, text
from config import Config

engine = create_engine(
    Config.DB_CONNECTION_STRING,
    echo=True,
    connect_args={
        "ssl":{
            "ssl_ca": "etc/ssl/cert/pem"
        }
    }
)

with engine.connect() as conn:
    result = conn.execute(text("select * from users"))
    print(result.all())
