import os

from bot import create_app

app = create_app(os.environ.get("FLASK_ENV", "default"))


@app.cli.command("set-commands")
def set_commands():
    """Register the Telegram '/' command menus (private + group scopes,
    Russian descriptions) — run once after deploying a release that adds
    or renames a command. See bot/commands.py."""
    from bot.telegram_bot import bot
    from bot.commands import register_commands

    result = register_commands(bot)
    print(f"Telegram commands: {result}")


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
