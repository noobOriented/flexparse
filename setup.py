from pathlib import Path
from setuptools import setup, find_packages


readme = Path(__file__).parent / 'README.md'
if readme.exists():
    long_description = readme.read_text()
else:
    long_description = '-'


setup(
    name='flexparse',
    description='flexible argparse for scripts with many options.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
    packages=find_packages(),
    author='noobOriented',
    author_email='jsaon92@gmail.com',
    url='',
    license='MIT',
    install_requires=[],
)
