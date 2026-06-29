from pathlib import Path

import click
import yaml

from app import cli, slack
from pydantic_settings_manager import UserConfigError, load_user_configs


@click.command()
@click.argument("message", type=str)
@click.option("--channel", type=str, default=None)
@click.option("--slack-settings-key", type=str, default=None)
@click.option("--verbose", is_flag=True, default=None)
def main(
    message: str,
    channel: str | None,
    slack_settings_key: str | None,
    verbose: bool | None,
):
    user_configs_path = Path(__file__).parent.parent.parent / "settings.yaml"

    if user_configs_path.exists():
        with user_configs_path.open("r") as f:
            user_configs_dict = yaml.safe_load(f)

        # Apply user configs to all settings managers
        load_user_configs(user_configs_dict)

    # Apply CLI arguments to the settings manager
    if verbose is not None:
        cli.settings_manager.set_cli_args("verbose", verbose)

        # For nested keys, you can specify a dot-separated path
        # cli.settings_manager.set_cli_args("nested.value", "test")

        # To update the whole CLI args at once, pass a dict
        # cli.settings_manager.cli_args = {"verbose": True, "nested.value": "test"}

    try:
        # Get the settings class with the priority: CLI args > user configs > environment variables
        settings = cli.settings_manager.get_settings()

        if settings.verbose:
            click.echo("Verbose mode is enabled.")

        slack.send_slack_message(
            message, channel=channel, slack_settings_key=slack_settings_key
        )

    except UserConfigError as e:
        # Show only the friendly message on stderr (no traceback) and exit non-zero.
        click.secho(str(e), fg="red", err=True)
        raise SystemExit(1) from e
