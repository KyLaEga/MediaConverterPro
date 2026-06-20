import zipfile
import shutil
import re
import tempfile
import fitz
from pathlib import Path


class OptimizedMediaConverter:
    def __init__(self):
        self.valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp', '.gif')

    @staticmethod
    def _natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', str(s))]

    @staticmethod
    def _unique_path(path):
        """Return a non-existing path, adding a ' (2)', ' (3)'… suffix if needed."""
        if not path.exists():
            return path
        stem, suffix = path.stem, path.suffix
        i = 2
        while True:
            candidate = path.with_name(f"{stem} ({i}){suffix}")
            if not candidate.exists():
                return candidate
            i += 1

    def find_comics(self, source_paths):
        """Scans a list of paths (files or directories) and returns a list of targets."""
        targets = set()  # Use set to avoid duplicates
        
        for path_str in source_paths:
            source = Path(path_str)
            if not source.exists():
                continue
                
            if source.is_file():
                if source.suffix.lower() in ('.zip', '.cbz', '.pdf'):
                    targets.add(source)
            elif source.is_dir():
                # Check all files for zip/cbz/pdf
                for arch_file in source.rglob('*'):
                    if arch_file.is_file() and arch_file.suffix.lower() in ('.zip', '.cbz', '.pdf'):
                        targets.add(arch_file)
                        
                # Check directories for images (including the source dir itself)
                directories_to_check = [source] + [d for d in source.rglob('*') if d.is_dir()]
                for directory in directories_to_check:
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
            temp_extract = Path(tempfile.mkdtemp(prefix=f"comiconv_{source.stem}_"))
            try:
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract)
            except zipfile.BadZipFile:
                shutil.rmtree(temp_extract, ignore_errors=True)
                raise ValueError(f"Архив поврежден: {source.name}")
                
            images = [p for p in temp_extract.rglob('*') if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(str(x.relative_to(temp_extract))))
            return images, temp_extract

        elif source.suffix.lower() == '.pdf':
            temp_extract = Path(tempfile.mkdtemp(prefix=f"comiconv_{source.stem}_"))
            try:
                doc = fitz.open(source)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Use a moderate zoom for good reading quality (e.g., 2.0 = 144 DPI)
                    zoom = 2.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    out_path = temp_extract / f"page_{page_num + 1:04d}.png"
                    pix.save(str(out_path))
                doc.close()
            except Exception as e:
                shutil.rmtree(temp_extract, ignore_errors=True)
                raise ValueError(f"Ошибка при чтении PDF {source.name}: {e}")

            images = [p for p in temp_extract.rglob('*') if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(str(x.relative_to(temp_extract))))
            return images, temp_extract
            
        elif source.is_dir():
            # Only direct images: nested image folders are separate targets (see find_comics),
            # so recursing here would duplicate their pages into the parent's output.
            images = [p for p in source.iterdir() if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(x.name))
            return images, None
        else:
            raise ValueError(f"Неизвестный тип источника: {source.name}")

    def cleanup(self, temp_dir):
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def to_cbz(self, images, filename, output_dir, base_dir=None):
        if not images:
            raise FileNotFoundError("Изображения не найдены.")

        cbz_path = self._unique_path(Path(output_dir) / f"{filename}.cbz")

        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            for img in images:
                if base_dir:
                    arcname = str(img.relative_to(base_dir))
                else:
                    arcname = img.name
                cbz.write(img, arcname=arcname)
        
        return cbz_path

    def to_pdf(self, images_paths, filename, output_dir):
        if not images_paths:
            raise FileNotFoundError("Изображения не найдены.")

        pdf_path = self._unique_path(Path(output_dir) / f"{filename}.pdf")

        doc = fitz.open()
        try:
            for img_path in images_paths:
                try:
                    img_doc = fitz.open(img_path)
                    pdf_bytes = img_doc.convert_to_pdf()
                    img_doc.close()

                    page_doc = fitz.open("pdf", pdf_bytes)
                    doc.insert_pdf(page_doc)
                    page_doc.close()
                except Exception:
                    # Skip a single broken image instead of failing the whole document.
                    continue

            if doc.page_count == 0:
                raise ValueError("Не удалось добавить ни одной страницы в PDF.")

            doc.save(pdf_path)
        finally:
            doc.close()
        return pdf_path
