import zipfile
import shutil
import re
import tempfile
import fitz
import os
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

    def find_comics(self, source_paths, cancel_check=None):
        """Scans a list of paths (files or directories) and returns a list of targets."""
        targets = set()  # Use set to avoid duplicates
        
        for path_str in source_paths:
            if cancel_check and cancel_check():
                raise InterruptedError("Операция прервана")
            source = Path(path_str)
            if not source.exists():
                continue
                
            if source.is_file():
                if source.suffix.lower() in ('.zip', '.cbz', '.pdf'):
                    targets.add(source)
            elif source.is_dir():
                for root, dirs, files in os.walk(source):
                    if cancel_check and cancel_check():
                        raise InterruptedError("Операция прервана")

                    # Single pass: collect archives/PDFs and note any image in this dir.
                    has_images = False
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ('.zip', '.cbz', '.pdf'):
                            targets.add(Path(root) / f)
                        elif ext in self.valid_extensions:
                            has_images = True
                    if has_images:
                        targets.add(Path(root))
                            
        # Sort targets by name or absolute path for consistent ordering
        sorted_targets = list(targets)
        sorted_targets.sort(key=lambda x: self._natural_sort_key(x.name))
        return sorted_targets

    def extract_and_prepare(self, source_path, cancel_check=None):
        source = Path(source_path)
        if source.suffix.lower() in ('.zip', '.cbz'):
            temp_extract = Path(tempfile.mkdtemp(prefix=f"comiconv_{source.stem}_"))
            try:
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    infolist = zip_ref.infolist()
                    for member in infolist:
                        if cancel_check and cancel_check():
                            raise InterruptedError("Операция прервана")
                        
                        # Secure extraction to prevent Zip Slip (Directory Traversal)
                        target_path = (temp_extract / member.filename).resolve()
                        try:
                            target_path.relative_to(temp_extract)
                        except ValueError:
                            # Skip paths outside temp_extract
                            continue
                            
                        zip_ref.extract(member, temp_extract)
            except Exception as e:
                shutil.rmtree(temp_extract, ignore_errors=True)
                if isinstance(e, InterruptedError):
                    raise
                raise ValueError(f"Архив поврежден: {source.name}")
                
            images = [p for p in temp_extract.rglob('*') if p.is_file() and p.suffix.lower() in self.valid_extensions]
            images.sort(key=lambda x: self._natural_sort_key(str(x.relative_to(temp_extract))))
            return images, temp_extract

        elif source.suffix.lower() == '.pdf':
            temp_extract = Path(tempfile.mkdtemp(prefix=f"comiconv_{source.stem}_"))
            try:
                with fitz.open(source) as doc:
                    for page_num in range(len(doc)):
                        if cancel_check and cancel_check():
                            raise InterruptedError("Операция прервана")
                        page = doc.load_page(page_num)
                        # Use a moderate zoom for good reading quality but optimized for resource usage
                        zoom = 1.5
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        out_path = temp_extract / f"page_{page_num + 1:04d}.jpg"
                        pix.save(str(out_path))
            except Exception as e:
                shutil.rmtree(temp_extract, ignore_errors=True)
                if isinstance(e, InterruptedError):
                    raise
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

    def to_cbz(self, images, filename, output_dir, base_dir=None, cancel_check=None):
        return self._to_archive(images, filename, output_dir, "cbz", base_dir, cancel_check)

    def to_zip(self, images, filename, output_dir, base_dir=None, cancel_check=None):
        return self._to_archive(images, filename, output_dir, "zip", base_dir, cancel_check)

    def _to_archive(self, images, filename, output_dir, ext, base_dir=None, cancel_check=None):
        if not images:
            raise FileNotFoundError("Изображения не найдены.")

        out_path = self._unique_path(Path(output_dir) / f"{filename}.{ext}")

        try:
            with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as archive:
                for img in images:
                    if cancel_check and cancel_check():
                        raise InterruptedError("Операция прервана")
                    if base_dir:
                        arcname = str(img.relative_to(base_dir))
                    else:
                        arcname = img.name
                    archive.write(img, arcname=arcname)
        except Exception:
            # Clean up incomplete file
            if out_path.exists():
                out_path.unlink()
            raise

        return out_path

    def to_pdf(self, images_paths, filename, output_dir, cancel_check=None):
        if not images_paths:
            raise FileNotFoundError("Изображения не найдены.")

        pdf_path = self._unique_path(Path(output_dir) / f"{filename}.pdf")

        try:
            with fitz.open() as doc:
                for img_path in images_paths:
                    if cancel_check and cancel_check():
                        raise InterruptedError("Операция прервана")
                    try:
                        with fitz.open(img_path) as img_doc:
                            pdf_bytes = img_doc.convert_to_pdf()
                        with fitz.open("pdf", pdf_bytes) as page_doc:
                            doc.insert_pdf(page_doc)
                    except Exception:
                        # Skip a single broken image instead of failing the whole document.
                        continue

                if doc.page_count == 0:
                    raise ValueError("Не удалось добавить ни одной страницы в PDF.")

                doc.save(pdf_path)
        except Exception:
            # Clean up incomplete file
            if pdf_path.exists():
                pdf_path.unlink()
            raise
        return pdf_path
