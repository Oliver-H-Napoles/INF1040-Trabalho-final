"""
Script to merge all shapefiles in the data directory into a single coastline.shp file.
"""

import os
import fiona
from shapely.geometry import shape
from fiona.collection import Collection

def merge_shapefiles(input_dir, output_file):
    """
    Merge all shapefiles in input_dir into a single output shapefile.
    
    Args:
        input_dir: Directory containing the shapefiles
        output_file: Path to the output merged shapefile
    """
    
    # Find all .shp files in the input directory
    shp_files = [f for f in os.listdir(input_dir) if f.endswith('.shp')]
    
    if not shp_files:
        print(f"No shapefiles found in {input_dir}")
        return
    
    print(f"Found {len(shp_files)} shapefiles to merge")
    
    merged_features = []
    schema = None
    
    # Read all shapefiles and collect features
    for shp_file in sorted(shp_files):
        shp_path = os.path.join(input_dir, shp_file)
        print(f"Reading {shp_file}...")
        
        with fiona.open(shp_path) as src:
            if schema is None:
                schema = src.schema
            
            for feature in src:
                merged_features.append(feature)
    
    print(f"Total features: {len(merged_features)}")
    
    # Write merged features to output file
    print(f"Writing merged file to {output_file}...")
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with fiona.open(
        output_file,
        'w',
        driver='ESRI Shapefile',
        schema=schema,
        crs=None
    ) as dst:
        for feature in merged_features:
            dst.write(feature)
    
    print(f"Successfully merged shapefiles into {output_file}")


if __name__ == '__main__':
    # Define paths
    data_dir = os.path.join(os.path.dirname(__file__), '../../data')
    output_shapefile = os.path.join(data_dir, 'coastline.shp')
    
    merge_shapefiles(data_dir, output_shapefile)
