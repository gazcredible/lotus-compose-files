import setuptools
import shutil
import os

shutil.rmtree(os.getcwd()+'/build', ignore_errors=True)
shutil.rmtree(os.getcwd()+'/dist', ignore_errors=True)

with open('unexeaqua3s/README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='unexeaqua3s',
    version='4.0.0.6',
    author='Example Author',
    author_email='author@example.com',
    description='A small example package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pypa/sampleproject',
    # packages=setuptools.find_packages(),
    packages=['unexeaqua3s/.'],
    install_requires=['webdavclient3',
        'pyproj',
        'geopandas',
        'kml2geojson',
        'urllib3',
        'orjson',
        'pymoo==0.5.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
