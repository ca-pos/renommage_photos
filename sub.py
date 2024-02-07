from pathlib import Path

import rawpy
import imageio
import pyexiv2

class Photo():
    def __init__(self, file: str) -> None:
        path = Path(file)
        self.original_path = path.cwd()
        self.original_name = path.stem
        self.original_suffix = path.suffix
        
        meta_data = pyexiv2.ImageMetadata(file)
        meta_data.read()
        self.date = meta_data['Exif.Image.DateTimeOriginal'].value.strftime('%Y %m %d')
        self.orientation = meta_data['Exif.Image.Orientation'].value
        if self.original_suffix == '.NEF':
            self.nikon_file_number = meta_data['Exif.NikonFi.FileNumber'].value
        else:
            self.nikon_file_number = -1

        with rawpy.imread(file) as raw:
            self.thumb = raw.extract_thumb()
#################################################################################
