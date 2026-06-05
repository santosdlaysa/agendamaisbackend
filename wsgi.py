# IMPORTANTE: o monkey_patch do eventlet precisa rodar ANTES de qualquer outro
# import (Flask, SQLAlchemy, etc.), senão os locks do pool de conexões não viram
# "green" e o gunicorn com worker eventlet quebra com:
#   "cannot notify on un-acquired lock"
import eventlet
eventlet.monkey_patch()

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
