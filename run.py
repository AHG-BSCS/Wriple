from waitress import serve

from app.main import create_app, find_free_port

if __name__ == '__main__':
    port = find_free_port()
    app = create_app()
    # Electron will use this to load the app
    print(f"PORT:{port}", flush=True)
    # app.run(host='127.0.0.1', port=port, debug=True)
    serve(app, host='127.0.0.1', port=port)
