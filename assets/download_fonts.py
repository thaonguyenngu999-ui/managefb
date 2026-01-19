#!/usr/bin/env python3
"""
Script tải fonts cho FB Manager Pro
Fonts: Inter (UI), JetBrains Mono (Code)
"""
import os
import urllib.request
import zipfile
import shutil

FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

# Google Fonts download URLs
FONTS = {
    'Inter': 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip',
    'JetBrainsMono': 'https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip'
}

def download_fonts():
    """Tải và giải nén fonts"""
    os.makedirs(FONTS_DIR, exist_ok=True)

    for font_name, url in FONTS.items():
        print(f"Downloading {font_name}...")
        zip_path = os.path.join(FONTS_DIR, f'{font_name}.zip')

        try:
            urllib.request.urlretrieve(url, zip_path)
            print(f"  Extracting {font_name}...")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract only .ttf and .otf files
                for file in zip_ref.namelist():
                    if file.endswith(('.ttf', '.otf')) and 'static' in file.lower():
                        # Extract to fonts directory
                        filename = os.path.basename(file)
                        with zip_ref.open(file) as source:
                            target_path = os.path.join(FONTS_DIR, filename)
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                        print(f"    Extracted: {filename}")

            os.remove(zip_path)
            print(f"  {font_name} done!")

        except Exception as e:
            print(f"  Error downloading {font_name}: {e}")

    print("\nAll fonts downloaded to:", FONTS_DIR)
    print("\nTo install fonts on your system:")
    print("  Windows: Right-click .ttf files -> Install")
    print("  macOS: Double-click .ttf files -> Install Font")
    print("  Linux: Copy to ~/.fonts/ and run 'fc-cache -fv'")

if __name__ == '__main__':
    download_fonts()
