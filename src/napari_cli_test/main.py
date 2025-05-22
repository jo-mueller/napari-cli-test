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


_OUTPUT_FOLDER_PARAM_NAME = 'output_folder'


def make_cli_executable(function: Callable) -> Callable:

    sig = inspect.signature(function)
    params = list(sig.parameters.values())

    new_parameters = []
    for i, param in enumerate(params):
        if param.annotation == Image:
            overwritten_param = inspect.Parameter(
                param.name,
                param.kind,
                annotation=Path
            )
            new_parameters.append(overwritten_param)
        else:
            new_parameters.append(param)

    # append parameter "output_folder" with default value None to params
    output_folder_param = inspect.Parameter(
        name=_OUTPUT_FOLDER_PARAM_NAME,
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default='.',
        annotation=Path,
    )
    new_parameters.append(output_folder_param)

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """
        A wrapper function that makes a function executable from the command line.
        """

        # Check all replaced_params (which are of type Path) are provided and valid
        for param in new_parameters:
            if param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")

            param_value = os.path.abspath(kwargs[param.name])
            print(f"Parameter {param.name} has value: {param_value}")
            if not os.path.exists(param_value):
                raise ValueError(f"Invalid file path for parameter: {param.name}")

        if _OUTPUT_FOLDER_PARAM_NAME in kwargs:
            output_folder = kwargs[_OUTPUT_FOLDER_PARAM_NAME]
            kwargs.pop(_OUTPUT_FOLDER_PARAM_NAME)
        else:
            output_folder = os.path.abspath('.')

        # Read the image file(s)
        for param in new_parameters[:-1]:  # omit last parameter (output folder)
            kwargs[param.name] = Image(imread(kwargs[param.name]))

        result_layer = function(*args, **kwargs)

        # Save the result to a file
        output_file = os.path.join(output_folder, function.__name__ + '_output.tif')
        imsave(output_file, result_layer.data)

        return output_file

    # Update the wrapper's signature
    wrapper.__signature__ = sig.replace(
        parameters=new_parameters,
        return_annotation=Path
        )

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