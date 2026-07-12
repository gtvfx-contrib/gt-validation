"""Generate API reference pages for mkdocs, consumed by mkdocs-literate-nav.

Runs automatically as part of ``properdocs build`` via the
``mkdocs-gen-files`` plugin (see ``properdocs.yml``). Generates reference
pages for the main package and its public submodules.
"""

from __future__ import annotations

import mkdocs_gen_files

PACKAGES = [
    "gt.validator",
    "gt.validator.rules",
    "gt.validator.context",
    "gt.validator.reporting",
]

nav = mkdocs_gen_files.Nav()


def _writeModulePage(doc_path: str, module_name: str) -> None:
    """Write a single reference page containing a mkdocstrings directive.

    Args:
        doc_path: Virtual path (relative to the docs dir) to write to.
        module_name: Fully-qualified module name to document.

    """
    with mkdocs_gen_files.open(doc_path, "w") as doc_file:
        doc_file.write(f"# `{module_name}`\n\n::: {module_name}\n")


for package_name in PACKAGES:
    segments = tuple(package_name.split("."))
    doc_path = f"reference/{package_name}.md"
    _writeModulePage(doc_path, package_name)
    nav[segments] = f"{package_name}.md"

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
