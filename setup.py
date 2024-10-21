from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [line.strip() for line in fh.readlines() if line.strip()]

setup(
    name='ataims',
    version='0.0.2',
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
    py_modules=['ataims', 'tests'],
        entry_points={
        'console_scripts': [
            'ataims=ataims.__main__:main',
        ],
    },
)
