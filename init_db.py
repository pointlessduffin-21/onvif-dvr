from dotenv import load_dotenv
from database import init_db

if __name__ == '__main__':
    load_dotenv()
    init_db()
