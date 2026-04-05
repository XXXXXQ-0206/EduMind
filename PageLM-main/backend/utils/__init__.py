"""
Utility package.

Do not import provider-specific modules here. Importing ``utils`` happens before
submodules such as ``utils.auth`` or ``utils.storage`` are loaded, so eager
imports would force every optional AI provider to initialize during app startup.
"""

__all__: list[str] = []
