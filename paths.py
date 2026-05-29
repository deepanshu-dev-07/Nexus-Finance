"""Resolve data paths for dev (source) and frozen (PyInstaller .exe) runs."""
import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    return os.path.join(app_dir(), "data")


def db_path():
    return os.path.join(data_dir(), "finance.db")
