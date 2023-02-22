import setuptools

import shutil
import os

shutil.rmtree(os.getcwd()+'/build', ignore_errors=True)
shutil.rmtree(os.getcwd()+'/dist', ignore_errors=True)



with open('epanet_fiware/readme.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='epanet_fiware',
    version='2.0.0.25',
    author='Example Author',
    author_email='author@example.com',
    description='A small example package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pypa/sampleproject',
    # packages=setuptools.find_packages(),
    packages=['epanet_fiware'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=['jenkspy',
                      'matplotlib',
                      'scikit-build',
                      'cmake',
                      'owa-epanet',
                      'pandas',
                      'numpy',
                      ],
    python_requires='>=3.7',
)
