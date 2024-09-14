# Dot-to-Dot Image Processor

This project helps in creating a dot-to-dot version of an image:

![](test/test_demo.jpeg)

This tool processes an image to detect contours or paths and generates an output image with dots placed along them. It also adds labels to each dot and allows for additional customization such as dot color, radius, and distance between dots. For developers, an optional debug mode is available to display intermediate results.

## Installation

Before running the script, make sure to install the required Python libraries. You can install them using the provided `requirements.txt` file.

```
pip install -r requirements.txt
```

## Usage

Ensure you have Python 3.6 or newer installed on your system. Clone this repository or download the scripts and `requirements.txt` file. Install the required libraries as mentioned above. To use the script, run it from the command line with the desired options:

```
python main.py [options]
```

## Options

- `-i`, `--input` `<image>`: Specify the input image path or a folder of images to process. Defaults to `input.png`. If a folder is provided, all images inside will be processed.

- `-o`, `--output` `<image path>`: Specify the output image path or folder. If not provided, the input name with `_dotted` will be used.

- `-sd`, `--shapeDetection` `<method>`: Shape detection method to use. Choose between `"Contour"` or `"Path"`. Defaults to `"Contour"`.

- `-np`, `--numPoints` `<number>`: Desired number of points in the simplified path (applies to both methods). If not specified, all points after processing will be used.

- `-d`, `--distance` `<min> <max>`: Minimum and maximum distances between points as percentages of the image diagonal (e.g., `-d 0.01 0.05`).

- `-e`, `--epsilon` `<epsilon>`: Epsilon for path approximation. Defaults to `0.001`.

- `-f`, `--font` `<font file>`: Specify the font file name used for labeling. Searched automatically in `C:\Windows\Fonts`. Defaults to `Arial.ttf`.

- `-fs`, `--fontSize` `<size>`: Specify the font size for labeling the dots. Defaults to `48`.

- `-fc`, `--fontColor` `<r> <g> <b> <a>`: Specify the font color for labeling as 4 values in RGBA format (e.g., `0 0 0 255` for black). Defaults to `0 0 0 255`.

- `-dc`, `--dotColor` `<r> <g> <b> <a>`: Specify the dot color as 4 values in RGBA format (e.g., `0 0 0 255` for black). Defaults to `0 0 0 255`.

- `-r`, `--radius` `<radius>`: Specify the radius of the dots in pixels. Defaults to `20`.

- `--dpi` `<dpi>`: Specify the DPI (dots per inch) of the output image. Defaults to `400`.

- `-tb`, `--thresholdBinary` `<threshold> <max_value>`: Specify the threshold value and maximum value for binary thresholding. Defaults to `100 255`.

- `-de`, `--debug`: Enable debug mode to display intermediate steps such as the contours and dot placements.

- `-do`, `--displayOutput`: Display the output image after processing. Defaults to `True`.

- `-v`, `--verbose`: Enable verbose mode to print progress information during execution. Defaults to `True`.

## Examples

### Basic Usage

To process an image with default settings:

```
python main.py -i "my_image.png" 
```


## More about the placement of the dots

The placement of the dots is controlled by the `-sd` or `--shapeDetection` argument, which determines the method used to detect shapes in the image. There are two methods available:

- **Contour Method (`-sd Contour`)**: This method detects the contours in the image using OpenCV's contour detection algorithms. It approximates the contours of shapes in the image and places dots along these contours. This method is suitable for images with clear edges and distinct shapes.

- **Path Method (`-sd Path`)**: This method uses skeletonization to extract the central path or skeleton of the largest shape in the image. It is useful for images where you want to create a dot-to-dot path that follows the main structure or outline of the shape.

## More about the number of dots

The number of dots placed along the paths is influenced by several parameters that control the simplification and spacing of the points:

- **Epsilon (`-e`, `--epsilon`)**: This parameter controls the approximation accuracy for contour simplification. A smaller epsilon value results in a higher number of points (more detailed contours), while a larger epsilon value reduces the number of points by simplifying the contours more aggressively. Lowering the epsilon value increases the number of dots, capturing finer details of the shape.

- **Distance (`-d`, `--distance` `<min> <max>`)**: These values set the minimum and maximum distances between points as percentages of the image diagonal. The script enforces these distance constraints after simplifying the path. Points closer than the minimum distance will be removed, and midpoints will be inserted between points that are farther apart than the maximum distance. The distance parameters have priority over the desired number of points (`numPoints`).

- **Desired Number of Points (`-np`, `--numPoints`)**: This parameter specifies the desired number of points in the simplified path. The script will first attempt to simplify the path to approximately this number of points using the Visvalingam–Whyatt algorithm.

### Priority of Parameters

The script processes the number of dots in the following order:

1. **Initial Simplification**: The path is simplified to reach the desired number of points specified by `numPoints` using the epsilon value and simplification algorithms.

2. **Enforcing Distance Constraints**: After simplification, the script adjusts the points to satisfy the minimum and maximum distance requirements:

   - **Insertion of Midpoints**: If the distance between two consecutive points exceeds the maximum distance (`distance max`), additional points (midpoints) are inserted to reduce the spacing.

   - **Removal of Points**: If points are closer than the minimum distance (`distance min`), they are removed to increase the spacing.

Due to this process, the distance constraints have priority over the desired number of points. The script will adjust the number of dots by adding or removing points to ensure that all points meet the specified distance requirements, even if this means deviating from the initial `numPoints` value.
