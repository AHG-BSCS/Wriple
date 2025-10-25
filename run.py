import socket
import threading
import time

from waitress import create_server
import webview

from app.main import create_app, find_free_port


def _wait_for_server(host: str, port: int, timeout: float) -> None:
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


if __name__ == '__main__':
    port = find_free_port()
    app = create_app()
    host = '127.0.0.1'

    server = create_server(app, host=host, port=port)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    _wait_for_server(host, port, 10.0)

    window = webview.create_window('WRIPLE', f'http://{host}:{port}', width=1366, height=768, min_size=(300, 200))

    def _shutdown_server() -> None:
        server.close()
        server_thread.join(timeout=5)

    window.events.closed += _shutdown_server

    webview.start()
