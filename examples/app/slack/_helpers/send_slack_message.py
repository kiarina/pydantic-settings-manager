from .._settings import settings_manager


def send_slack_message(
    message: str,
    channel: str | None = None,
    slack_settings_key: str | None = None,
) -> None:
    # Get the settings class by key
    settings = settings_manager.get_settings(slack_settings_key)

    if channel is None:
        channel = settings.default_channel

    print(f"Sending message to Slack channel '{channel}': {message}")
