from api4be import create_app 

app = create_app()
app.run(debug=True, use_reloader=False)

