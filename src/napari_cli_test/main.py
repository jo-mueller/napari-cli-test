from typing import Callable, Union, get_args, get_origin
import importlib
from typing_extensions import Annotated
import functools
import inspect
from pathlib import Path
import os
import typer
from skimage import io
import numpy as np
from napari import layers, types
import npe2
from magicgui.type_map._magicgui import MagicFactory
from napari_cli_test.function import threshold_otsu, threshold_mean

app = typer.Typer()


_OUTPUT_FOLDER_PARAM_NAME = 'output_folder'

supported_inputs = [
    layers.Image,
    layers.Labels,
]

def parse_napari_image(value: Path) -> layers.Image:
    image = io.imread(value)
    return layers.Image(image, name=Path(value).stem)

def parse_napari_labels(value: Path) -> layers.Labels:
    labels = io.imread(value).astype(np.uint8)
    return layers.Labels(labels, name=Path(value).stem)

def is_optional(annotation):
    return (
        get_origin(annotation) is Union
        and type(None) in get_args(annotation)
    )

_WRITER_DISPATCH = {
    layers.Image: io.imsave,
    layers.Labels: io.imsave,
}

_READER_DISPATCH = {
    layers.Image: parse_napari_image,
    layers.Labels: parse_napari_labels,
}


def make_cli_executable(function: Callable) -> Callable:
    sig = inspect.signature(function)

    parameters = []
    for param in sig.parameters.values():
        if get_origin(param.annotation) is Union:
            annotation = [arg for arg in get_args(param.annotation) if arg is not type(None)][0]
        else:
            annotation = param.annotation

        if annotation in supported_inputs:
            parser = _READER_DISPATCH[annotation]
            
            # check if argument is optional or required
            if is_optional(param.annotation):
                new_annotation = Annotated[annotation, typer.Option(parser=parser)]
            else:
                new_annotation = Annotated[annotation, typer.Argument(parser=parser)]

            # Create a new parameter with the updated annotation
            overwritten_param = inspect.Parameter(
                param.name,
                param.kind,
                annotation=new_annotation
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

        # Apply and convert to layer if necessary
        result_layer = function(*args, **kwargs)
        if isinstance(result_layer, tuple):
            result_layer = layers.Layer.create(*result_layer)

        # Save to file
        output_file = output_folder / f"{function.__name__}_output.tif"
        _WRITER_DISPATCH[type(result_layer)](
            output_file,
            result_layer.data,
        )
        
        #result_layer.save(output_file, plugin=_WRITER_DISPATCH[type(result_layer)])

        return output_file

    # Update the wrapper's signature
    wrapper.__signature__ = sig.replace(
        parameters=parameters,
        return_annotation=Path
        )

    return wrapper


# Discover and register commands from the napari-skimage plugin
plugin_manager = npe2.PluginManager()
plugin_manager.discover()
manifest = plugin_manager.get_manifest('napari-skimage')

for idx, cmd in enumerate(manifest.contributions.commands):
    module_path, function_name = cmd.python_name.split(':')

    # Import the module
    module = importlib.import_module(module_path)

    # Get the function
    function = getattr(module, function_name)

    if inspect.isclass(function):
        continue

    if isinstance(function, MagicFactory):
        widget = function()
        function = widget._function

    if 'napari.viewer.Viewer' in [p.annotation for p in inspect.signature(function).parameters.values()]:
        continue

    try:
        app.command()(make_cli_executable(function))
    except Exception as e:
        continue




app.command()(make_cli_executable(threshold_otsu))
app.command()(make_cli_executable(threshold_mean))
app.command()(make_cli_executable(threshold_manual))

if __name__ == "__main__":
    app()