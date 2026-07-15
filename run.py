import os

from app import create_app
from dotenv import load_dotenv
load_dotenv()


app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)
