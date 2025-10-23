from app.main import create_app, find_free_port

if __name__ == '__main__':
    port = find_free_port()
    app = create_app()
    print(f"PORT:{port}", flush=True)   # Electron will read this
    app.run(host='127.0.0.1', port=port, debug=False)
