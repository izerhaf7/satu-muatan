"""Pastikan package `app` ter-import walau pytest dijalankan dari luar folder backend."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
