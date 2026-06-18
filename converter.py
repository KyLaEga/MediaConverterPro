import os
import zipfile
import shutil
import re
from pathlib import Path
from PIL import Image, ImageOps

class OptimizedMediaConverter:
    def __init__(self):
        self.valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.tiff')

    @staticmethod
    def _natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', str(s))]

    def find_comics(self, source_paths):
        """Scans a list of paths (files or directories) and returns a list of targets."""
        targets = set()  # Use set to avoid duplicates
        
        for path_str in source_paths:
            source = Path(path_str)
            if not source.exists():
                continue
                
            if source.is_file():
                if source.suffix.lower() in ('.zip', '.cbz'):
                    targets.add(source)
            elif source.is_dir():
                # Check all files for zip/cbz
                for arch_file in source.rglob('*'):
                    if arch_file.is_file() and arch_file.suffix.lower() in ('.zip', '.cbz'):
                        targets.add(arch_file)
                        
                # Check directories for images (including the source dir itself)
                directories_to_check = [source] + [d for d in source.rglob('*') if d.is_dir()]
                for directory in directories_to_check:
                    if "temp_extract" not in directory.name:
                        has_images = any(p.suffix.lower() in self.valid_extensions for p in directory.iterdir() if p.is_file())
                        if has_images:
                            targets.add(directory)
                            
        # Sort targets by name or absolute path for consistent ordering
        sorted_targets = list(targets)
        sorted_targets.sort(key=lambda x: self._natural_sort_key(x.name))
        return sorted_targets

    def extract_and_prepare(self, source_path):
        source = Path(source_path)
        if source.suffix.lower() in ('.zip', '.cbz'):
            temp_extract = Path(f"temp_extract_{source.stem}_{os.urandom(4).hex()}")
            temp_extract.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract)
            except zipfile.BadZipFile:
                shutil.rmtree(temp_extract, ignore_errors=True)
                raise ValueError(f"Архив поврежден: {source.name}")
                
            images = [p for p in temp_extract.rglob('*') if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(x.name))
            return images, temp_extract
            
        elif source.is_dir():
            images = [p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(x.name))
            return images, None
        else:
            raise ValueError(f"Неизвестный тип источника: {source.name}")

    def cleanup(self, temp_dir):
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def to_cbz(self, images, filename, output_dir):
        cbz_path = Path(output_dir) / f"{filename}.cbz"
        
        if not images:
            raise FileNotFoundError("Изображения не найдены.")

        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            for img in images:
                cbz.write(img, arcname=img.name)
        
        return cbz_path

    def _pdf_image_generator(self, image_paths):
        for img_path in image_paths[1:]:
            with Image.open(img_path) as img:
                img = ImageOps.exif_transpose(img)
                clean_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    alpha_img = img.convert('RGBA')
                    clean_img.paste(alpha_img, mask=alpha_img.split()[3])
                else:
                    clean_img.paste(img.convert('RGB'))
                yield clean_img

    def to_pdf(self, images_paths, filename, output_dir):
        pdf_path = Path(output_dir) / f"{filename}.pdf"
            
        if not images_paths:
            raise FileNotFoundError("Изображения не найдены.")

        with Image.open(images_paths[0]) as first_img:
            first_img = ImageOps.exif_transpose(first_img)
            clean_first = Image.new("RGB", first_img.size, (255, 255, 255))
            if first_img.mode in ('RGBA', 'LA') or (first_img.mode == 'P' and 'transparency' in first_img.info):
                alpha_first = first_img.convert('RGBA')
                clean_first.paste(alpha_first, mask=alpha_first.split()[3])
            else:
                clean_first.paste(first_img.convert('RGB'))
            
            clean_first.save(
                pdf_path, 
                format="PDF",
                save_all=True, 
                append_images=self._pdf_image_generator(images_paths),
                resolution=100.0 
            )

        return pdf_path
