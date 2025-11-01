import socket
import threading
import time

from waitress import create_server
import webview

from app.main import create_app


def _wait_server(timeout = 10.0):
    """Poll until the Waitress server starts accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.1)
    raise RuntimeError(f"Server at {host}:{port} did not start within {timeout} seconds")

def _setup_window():
    """Set up and run the webview window with the Flask app backend."""
    _wait_server()
    window = webview.create_window(
        'WRIPLE',
        f'http://{host}:{port}',
        width=1366, height=775,
        min_size=(300, 200),
        zoomable=True
    )

    def _shutdown_server() -> None:
        server.close()
        server_thread.join(timeout=5)

    window.events.closed += _shutdown_server
    webview.start()

def _find_port(host):
    """Find an available port on the host machine."""
    s = socket.socket()
    s.bind((host, 0))
    _, port = s.getsockname()
    s.close()
    return port

if __name__ == '__main__':
    app = create_app()
    host = '127.0.0.1'
    port = _find_port(host)
    print(f'APP: http://{host}:{port}')

    server = create_server(app, host=host, port=port)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    _setup_window()
