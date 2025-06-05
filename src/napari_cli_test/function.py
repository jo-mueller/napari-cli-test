
from napari.layers import Image, Labels


def threshold_otsu(image: Image) -> Labels:
    print(f"Processing image with shape: {image.data.shape}")
    from skimage import filters

    threshold = filters.threshold_otsu(image.data)
    binary = image.data > threshold
    return Labels(binary)


def threshold_mean(image: Image) -> Labels:
    print(f"Processing image with shape: {image.data.shape}")

    threshold = image.data.mean()
    binary = image.data > threshold
    return Labels(binary)


def threshold_manual(image: Image, threshold: float) -> Labels:
    print(f"Processing image with shape: {image.data.shape}")

    binary = image.data > threshold
    return Labels(binary)