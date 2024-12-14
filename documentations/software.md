# Software Presentation: Dot to Dot

Welcome to **Dot to Dot**, a comprehensive tool designed to transform your favorite images into engaging dot-to-dot puzzles. This document serves as an exhaustive guide to help you understand and use every aspect of the software effectively.

---

## Main GUI Overview

The main graphical interface (GUI) is your primary workspace for managing inputs, processing images, and customizing your dot-to-dot creations.

### 1. Control Panel

The **Control Panel** is located on the right side of the main GUI. It provides access to critical tools and settings:

- **Shape Detection Mode**: Choose between:
  - **Automatic**: Automatically selects the best detection mode for your image.
  - **Contour**: Best for shapes with enclosed areas (e.g., circles, polygons).
  - **Path**: Suitable for open shapes with distinct start and endpoints.
- **Buttons**:
  - **Shape Visualization Window**: Opens a window to view the detected shapes (see details below).
  - **Dots Disposition Window**: Opens a window to adjust the placement and distribution of dots (see details below).
  - **Process**: Processes the input image using the current settings.

### 2. Menu Bar

The **Menu Bar** offers additional functionality:

#### **File Menu**
- **Open**: Load an image or a `.d2d` project file (Dot to Dot format for saving edits).
- **Save** and **Save As**: Save your project. The default format is `.d2d`, allowing for future re-editing. You can also save as `.png` directly.
- **Export As**: Save the processed dot-to-dot image as a `.png` or `.jpg`.
- **Exit**: Close the application.

#### **Edit Menu**
- **Dot and Label Aspect**: Configure dot radius, dot color, label font, label font size, and label color.
- **Process**: Processes the input image with the defined parameters.
- **Edit**: Opens the **Edit Window** for fine-tuning your dot-to-dot project.

#### **Preference Menu**
- **Default Settings**: Set default parameters for dot radius, font size, colors, and other preferences.

#### **Help Menu**
- Access help documentation and troubleshooting options.

### 3. Input Preview

The **Input Preview** displays the image currently loaded. Features include:
- **Double-Click**: Opens a file browser to load a `.png` or `.d2d` file.
- **Panning**: Hold the left mouse button and drag to pan the view.
- **Zooming**: Use the mouse wheel to zoom in and out.

### 4. Output Preview

The **Output Preview** shows the processed dot-to-dot image. Features include:
- **Double-Click**:
  - Before processing: Automatically processes the input with current parameters.
  - After processing: Opens the **Edit Window** for manual adjustments.
- **Panning**: Hold the left mouse button and drag to pan.
- **Zooming**: Use the mouse wheel to zoom in and out.

---

## Edit Window

The **Edit Window** provides advanced tools for refining your dot-to-dot creations.

### 1. Main View

The **Main View** displays the dot-to-dot image and allows for:
- **Moving Dots and Labels**: Drag dots or labels to reposition them.
- **Panning**: Hold the right mouse button and drag to pan.
- **Zooming**: Use the mouse wheel to zoom in and out.
- **Deleting Dots**: Click a dot and press `Delete`.
- **Adding Dots**: Double-click between two dots to add a new one.
- **Overlap Indication**: Overlapping dots or labels are highlighted in red.

### 2. Dot Control Panel

Located on the right side of the **Edit Window**, the **Dot Control Panel** provides various options:
- **Add**: Add new dots.
- **Remove**: Remove specific dots.
- **Radius for One Dot**: Adjust the radius of a single dot.
- **Order**: Modify the starting dot in the sequence.
- **Direction**: Reverse the order of dots.
- **Link Dots**: Toggle lines connecting successive dots.
- **Dot Radius**: Adjust the radius of all dots.
- **Font Size**: Adjust the size of dot labels.
- **Show Labels**: Toggle the visibility of labels.
- **Opacity**: Adjust the background opacity.
- **Browse Background**: Choose a custom background image (default is the input image).

### 3. Apply Changes

After making adjustments, click **Apply** to save changes and update the dot-to-dot image.

---

## Dots Disposition Window

The **Dots Disposition Window** allows you to adjust dot distribution and spacing.

### 1. Main View

The main view provides a preliminary visualization of the dot-to-dot image. Features include:
- **Panning**: Hold the left mouse button and drag to pan.
- **Zooming**: Use the mouse wheel to zoom in and out.

### 2. Controls

- **Opacity Slider**: Adjust the opacity of the background image.
- **Epsilon Slider**: Modify the level of detail by increasing or decreasing the number of dots.
- **Enable Distance Between Dots Configuration**:
  - When enabled, displays two additional sliders:
    - **Maximum Distance**: Set the maximum allowable distance between dots.
    - **Minimum Distance**: Set the minimum allowable distance between dots.

---

## Shape Visualization Window

The **Shape Visualization Window** displays the detected shapes in the input image.

### 1. Main View

The main view shows the detected shapes. Features include:
- **Panning**: Hold the left mouse button and drag to pan.
- **Zooming**: Use the mouse wheel to zoom in and out.

### 2. Controls

- **Opacity Slider**: Adjust the opacity of the background image.
- **Shape Mode Detection**:
  - **Automatic**: Automatically selects the best detection mode.
  - **Contour**: Detects closed shapes (e.g., circles, polygons).
  - **Path**: Detects open shapes with distinct start and endpoints.

---

This comprehensive guide should help you get started with **Dot to Dot** and unlock its full potential for creating engaging dot-to-dot puzzles. For more advanced features or command-line usage, refer to the [Advanced Usage](./Advanced_Usage.md) document.