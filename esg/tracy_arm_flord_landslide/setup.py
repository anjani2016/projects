from setuptools import setup, find_packages

setup(
    name="tracy_arm_tsunami_twin",
    version="0.1.0",
    description="Digital Twin for Tracy Arm Fjord Landslide-Generated Tsunami Simulation",
    author="Anjani",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.32",
        "numpy>=1.26",
        "scipy>=1.12",
        "plotly>=5.20",
        "pyvista>=0.43",
        "rasterio>=1.3",
        "geopandas>=0.14",
        "shapely>=2.0",
        "requests>=2.31",
        "pyproj>=3.6",
        "pydeck>=0.8",
    ],
    python_requires=">=3.10",
)
