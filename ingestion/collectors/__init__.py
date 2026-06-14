"""Collectors package — import triggers registration of all sources (SDS-043)."""

import importlib
import pkgutil

for _, module_name, _ in pkgutil.walk_packages(__path__, __name__ + "."):
    importlib.import_module(module_name)


