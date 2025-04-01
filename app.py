from app_init import app
from flask.cli import AppGroup
from post_scheduler import main

# Flask CLI コマンドの登録
scheduler_cli = AppGroup("run_scheduler")

@scheduler_cli.command("run")
def run_scheduler():
    print("📅 Running scheduled posts...")
    main()

# Flaskアプリに CLI コマンド登録
app.cli.add_command(scheduler_cli)

if __name__ == "__main__":
    app.run(debug=True)
