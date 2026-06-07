# Practical guide to Rasterio.

Think of Rasterio as your translator between the geographical world (coordinates, projections, real-world scale) and the mathematical world (pure numbers in a grid). It is built on top of the powerful GDAL library but wraps it in a much more user-friendly, "Pythonic" way.

Core Functionalities
For your Sea Level Rise Simulator, Rasterio will handle three main jobs:

I/O (Input/Output): Opening your .tiff files efficiently without crashing your computer's memory.

Metadata Extraction: Reading the spatial information—like the Coordinate Reference System (CRS), the physical size of the pixels, and the bounding box of the map.

Masking/Clipping: Taking a geometric polygon (like a state border from a .shp file) and "cookie-cutting" your raster to isolate that specific area.

The General Syntax
The absolute most important rule of Rasterio syntax is to always use a context manager (the with statement).

Raster files can be massive. If you open a file and forget to close it, it will lock up your system memory. The with block ensures the file is safely closed the moment your code finishes extracting what it needs.

Python
import rasterio

# The standard syntax for opening a raster file
with rasterio.open('caminho/para/seu/arquivo.tiff') as dataset:
    # Do your metadata extraction and reading inside this block
    pass 
Quick Code Cheat Sheet
Here are the specific snippets you will need for your project's modules.

## 1. Reading Metadata (For Módulo Validação)
Before you do any math, you need to validate that the raster has the correct spatial data.

~~~
Python
import rasterio

with rasterio.open('terreno.tiff') as dataset:
    print(dataset.name)        # File path/name
    print(dataset.count)       # Number of bands (usually 1 for elevation)
    print(dataset.width)       # Number of columns
    print(dataset.height)      # Number of rows
    print(dataset.crs)         # Coordinate Reference System (e.g., EPSG:4326)
    print(dataset.transform)   # The math that maps pixels to real-world coordinates
~~~

## 2. Extracting the Matrix (For Módulo Água)
This is how you cross the bridge from Rasterio into NumPy. You read a specific "band" (layer) of the raster. Topography data is usually a single band.
~~~
Python
import rasterio

with rasterio.open('terreno.tiff') as dataset:
    # Read the first band into a 2D NumPy array
    matriz_terreno = dataset.read(1)

# Now you are outside the 'with' block. 
# The file is closed, but 'matriz_terreno' is safely stored in memory as a standard matrix!
~~~
## 3. Masking/Isolating an Area (For Módulo Terreno)
To isolate a specific state, you will use rasterio.mask. You pass it the open dataset and a list of shapes (polygons), and it returns a new matrix where everything outside the shape is hidden or replaced.
~~~
Python
import rasterio
from rasterio.mask import mask
import geopandas as gpd

# 1. Load your boundary (using GeoPandas for the .shp file)
fronteiras = gpd.read_file('fronteira.shp')
geometria_estado = fronteiras.geometry # This is the polygon

with rasterio.open('terreno.tiff') as dataset:
    # 2. Apply the mask
    # 'nodata=10000' fills the outside area with your barrier value
    matriz_delimitada, transformacao_mascara = mask(
        dataset, 
        geometria_estado, 
        crop=True, 
        nodata=10000 
    )

# matriz_delimitada is now a NumPy array with the outside blocked off!
~~~
### Pro-Tip for your Validation Module
Rasterio matrices often load with a third dimension for the "bands" (e.g., shape (1, 1000, 1000) instead of (1000, 1000)). If your valida_matrizes_tamanho function is failing because of dimensions, you might need to use matriz_terreno[0] to grab just the 2D grid!
