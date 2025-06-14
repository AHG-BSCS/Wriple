import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import create_app

if __name__ == '__main__':
    app = create_app()
    app.run()
