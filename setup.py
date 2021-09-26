import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zeroapi",
    version="0.0.1",
    author="Azizul Haque Ananto",
    description="Zero is a RPC framework to build fast and high performance Python microservices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    package_dir={'':'.'},
    install_requires=['pyzmq', 'msgpack']
)