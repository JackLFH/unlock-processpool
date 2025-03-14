import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unlock-processpool-win",
    version="1.0.2",
    author="Half open flowers",
    author_email="1816524875@qq.com",
    description="Unlock ProcessPoolExecutor's worker limit on Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/unlock-processpool-win",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=[],
    include_package_data=True,
)