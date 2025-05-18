from typing import Callable
import functools
import inspect
from pathlib import Path
import os
import typer
from skimage.io import imread, imsave
from napari.layers import Image, Labels
from napari_cli_test.function import threshold_otsu, threshold_mean

app = typer.Typer()


def make_cli_executable(function: Callable) -> Callable:

    sig = inspect.signature(function)
    params = list(sig.parameters.values())

    replaced_params = []

    for i, param in enumerate(params):
        if param.annotation == Image:
            params[i] = inspect.Parameter(
                param.name,
                param.kind,
                annotation=Path
            )
            replaced_params.append(param.name)

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """
        A wrapper function that makes a function executable from the command line.
        """

        # Check all replaced_params (which are of type Path) are provided and valid
        for param_name in replaced_params:
            if param_name not in kwargs:
                raise ValueError(f"Missing required parameter: {param_name}")

            param_value = os.path.abspath(kwargs[param_name])
            print(f"Parameter {param_name} has value: {param_value}")
            if not os.path.exists(param_value):
                raise ValueError(f"Invalid file path for parameter: {param_name}")

        # Read the image file(s)
        for param_name in replaced_params:
            kwargs[param_name] = Image(imread(kwargs[param_name]))

        result_layer = function(*args, **kwargs)

        # Save the result to a file
        output_file = function.__name__ + '_output.tif'
        imsave(output_file, result_layer.data)

        return output_file

    # Update the wrapper's signature
    wrapper.__signature__ = sig.replace(parameters=params, return_annotation=Path)

    # Update the wrapper's annotations
    wrapper.__annotations__ = {
        param.name: (Path if param.annotation == Image else param.annotation)
        for param in sig.parameters.values()
    }
    wrapper.__annotations__['return'] = Path

    return wrapper


app.command()(make_cli_executable(threshold_otsu))
app.command()(make_cli_executable(threshold_mean))

if __name__ == "__main__":
    app()