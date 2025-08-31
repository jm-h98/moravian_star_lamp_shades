# Lampshade Generator for A1e Moravian Star (Herrnhuter Stern)

This script is for interactively generating lamp shades that can be 3D printed and pressure fit the default A1e moravian star mount (e.g. [Herrnhuter Stern](https://shop.herrnhuter-sterne.de/Stars-made-of-plastic/Stars-for-Indoor-Use/A1e-13cm-plastic-color-selection::9.html)).

You can test the designs for yourself in the browser: https://gestalte-deinen-lampenschirm.de.
If you want to create the stl corresponding to your online design, you can export the parameters and save them to a file, then import them into either the Processing or Python generator.
Alternatively, you can design the lamp shades in the Processing or python GUI and directly export the STLs.

There are currently 13 different designs that can be further modified:

## Preview

<p align="center">
  <img src="images/spirals.jpg" alt="Spirals" width="45%">
  <img src="images/ripples.jpg" alt="Ripples" width="45%">
</p>

<p align="center">
  <img src="images/default.jpg" alt="Default design" width="30%">
  <img src="images/shards.jpg" alt="Shards" width="30%">
  <img src="images/translucent.jpg" alt="Spirals (translucent PETG)" width="30%">
</p>
<p align="center">
  <img src="images/crosshatch.jpg" alt="Crosshatch" width="30%">
  <img src="images/double_sine.jpg" alt="Double Sine" width="30%">
  <img src="images/michelin.jpg" alt="Michelin" width="30%">
</p>
<p align="center">
  <img src="images/moire.jpg" alt="Moire" width="30%">
  <img src="images/michelin_spitz.jpg" alt="Michelin (Spitz)" width="30%">
  <img src="images/ridges.jpg" alt="Ridges" width="30%">
</p>
<p align="center">
  <img src="images/weave.jpg" alt="Weave" width="30%">
  <img src="images/twisted_pulse.jpg" alt="Twisted Pulse" width="30%">
  <img src="images/michelin_spirale.jpg" alt="Michelin (Spirale)" width="30%">
</p>


## Processing Version

<p align="center">
  <img src="images/screenshot_processing.png" alt="Screenshot of Processing GUI" width="75%">
</p>

### Installation

Install the official version of Processing from the [download page](https://processing.org/download).
Then just open `./app_processing/app_processing.pde` in Processing and hit play.


## Python version

<p align="center">
  <img src="images/screenshot_python.png" alt="Screenshot of Python GUI" width="75%">
</p>

### Installation

```bash
# Clone the github repo and go to the default directory
git clone git@github.com:jm-h98/moravian_star_lamp_shades.git
cd ./moravian_star_lamp_shades
pip install -r requirements.txt
python app.py
```


# Usage

The generator is based on a basic shape that is modulated by a design offset that modifies the radius at each point of the lamp shade.
The detail (resolution) value should be turned up to the max if you want a smooth print- however, lower values help modeling the lamp shade by reducing lag.
The overhang angle can be changed depending on what your specific printer is capable of and changes the connection between the mounting piece and the design part.
Keep in mind that extreme values in the design parameters may result in overhang angles that are larger than the specified value and thus not printable.
The generator allows for adapting many parameters:

### Basic shape

The {Top|Middle|Bottom} diameter control the lamp shades shape at the top (below the mounting piece), the middle and the very bottom. 
The rest of the shape is interpolated using these three values by linear, bezier and lagrangian interpolation.
The height of the lamp shade can also be controlled.

### Design

There are 12 different designs that are applied to the default shape that can be selected.
For each design, the number of features (e.g., how many spirals there are) can be modified as well as the feature depth (to modify the extend to which a design is deviating from the default radius).
Although there are mechanisms in place to keep the design offset from interfering wwith the mounting piece and the light bulb, keep in mind that, depending on your specific A1e hardware, extreme values might block the path of the light bulb. 
You can use your slicer to double-check.

# Printing the lamp shades

The stl files are solid and meant to be printed in vase mode for optimal translucency and minimal seams/layer lines.

I recommend printing at 0.16mm at 0.4mm nozzle size.
For BambuLab printers I have found these changes to the 0.16mm Standard profile to result in an optimal result:
- Spiral vase = true
- Smooth spiral = true
- Initial Line Width = 0.6
- Line width = 0.55

You can find the full BambuLab print profile on [MakerWorld](https://makerworld.com/en/models/1750381-lamp-shades-for-moravian-star-herrnhuter-stern#profileId-1860826).