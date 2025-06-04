from typing import Callable
from typing_extensions import Annotated
import functools
import inspect
from pathlib import Path
import os
import typer
from skimage import io
from napari import layers
from napari_cli_test.function import threshold_otsu, threshold_mean

app = typer.Typer()


_OUTPUT_FOLDER_PARAM_NAME = 'output_folder'

def parse_napari_image(value: Path) -> layers.Image:
    image = io.imread(value)
    return layers.Image(image, name=Path(value).stem)


def make_cli_executable(function: Callable) -> Callable:
    sig = inspect.signature(function)

    parameters = []
    for param in sig.parameters.values():
        if param.annotation == layers.Image:
            overwritten_param = inspect.Parameter(
                param.name,
                param.kind,
                annotation=Annotated[layers.Image, typer.Argument(parser=parse_napari_image)]
            )
            parameters.append(overwritten_param)
        else:
            parameters.append(param)

    # append parameter "output_folder" with default value None to params
    parameters.append(
        inspect.Parameter(
            name=_OUTPUT_FOLDER_PARAM_NAME,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default='.',
            annotation=Path,
        )
    )

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """
        A wrapper function that makes a function executable from the command line.
        """
        if _OUTPUT_FOLDER_PARAM_NAME in kwargs:
            output_folder = Path(kwargs.pop(_OUTPUT_FOLDER_PARAM_NAME))
        else:
            output_folder = Path('.')

        # Apply and then Save the result to a file
        result_layer = function(*args, **kwargs)
        output_file = output_folder / f"{function.__name__}_output.tif"
        io.imsave(output_file, result_layer.data)

        return output_file

    # Update the wrapper's signature
    wrapper.__signature__ = sig.replace(
        parameters=parameters,
        return_annotation=Path
        )

    return wrapper


app.command()(make_cli_executable(threshold_otsu))
app.command()(make_cli_executable(threshold_mean))

if __name__ == "__main__":
    app()