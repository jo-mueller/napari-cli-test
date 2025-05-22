from typer.testing import CliRunner
from ..main import app  # Import your Typer app

runner = CliRunner()


def test_cli_invoke():
    result = runner.invoke(app, ["threshold-otsu", 'human_mitosis.tif'])
    print(result)