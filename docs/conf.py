#!/usr/bin/env python3
import subprocess

try:
    from importlib.metadata import version as import_version
except ImportError:
    from importlib_metadata import version as import_version

extensions = [
    "sphinx.ext.autodoc",
    "jaraco.packaging.sphinx",
    "rst.linker",
    "sphinx_toolbox.collapse",
    "sphinx_toolbox.more_autodoc.autonamedtuple",
]

master_doc = "index"

link_files = {
    "../CHANGES.rst": dict(
        using=dict(GH="https://github.com"),
        replace=[
            dict(
                pattern=r"(Issue #|\B#)(?P<issue>\d+)",
                url="{package_url}/issues/{issue}",
            ),
            dict(
                pattern=r"(?m:^((?P<scm_version>v?\d+(\.\d+){1,2}))\n[-=]+\n)",
                with_scm="{text}\n{rev[timestamp]:%d %b %Y}\n",
            ),
            dict(
                pattern=r"PEP[- ](?P<pep_number>\d+)",
                url="https://peps.python.org/pep-{pep_number:0>4}/",
            ),
        ],
    )
}

# Be strict about any broken references:
nitpicky = True
nitpick_ignore = [
    ("py:class", "_asyncio.Task"),
    ("py:class", "pylsl.pylsl.XMLElement"),
]

# Include Python intersphinx mapping to prevent failures
# jaraco/skeleton#51
extensions += ["sphinx.ext.intersphinx"]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pupil_labs.realtime_api": (
        "https://pupil-labs-realtime-api.readthedocs.io/en/stable/",
        None,
    ),
}

html_theme = "furo"
autosummary_generate = True

project = "Pupil Labs LSL Relay"
release = import_version("lsl_relay")
# for example take major/minor
version = ".".join(release.split(".")[:2])
html_title = f"{project} {release}"

output = subprocess.check_output(
    ["python", "device_vs_lsl_sync.py"], cwd="../examples/"
)
print(output.decode())
