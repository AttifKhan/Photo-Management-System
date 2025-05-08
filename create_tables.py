from app.db.models import Base
from app.db.engine import engine

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    print('Tables created successfully')
