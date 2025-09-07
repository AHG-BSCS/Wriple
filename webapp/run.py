from app.main import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=3000)
