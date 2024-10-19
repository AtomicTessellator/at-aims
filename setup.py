from setuptools import setup, find_packages

from ataims.version import __version__


with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [line.strip() for line in fh.readlines() if line.strip()]

setup(
    name='outputparser',
    version=__version__,
    packages=find_packages(),
    description='A parser for FHI-aims output files',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AtomicTessellator/at-aims',
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    py_modules=['outputparser', 'tests'],
        entry_points={
        'console_scripts': [
            'outputparser=outputparser.__main__:main',
        ],
    },
)
