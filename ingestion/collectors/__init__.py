"""Collectors package — import triggers registration of all sources (SDS-043)."""

import importlib
import pkgutil

for info in pkgutil.walk_packages(__path__, __name__ + "."):
    importlib.import_module(info.name)


