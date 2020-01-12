from setuptools import setup
import os

try:
    with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
        long_description = f.read()
except Exception:
    long_description = ''

setup(
    name='seaborn-glowforge',
    version='6.2.0',
    description='SeabornGlowforge take a diagram (txt) file and draws the lines'
                ' needed to cut the floors and walls out for making a model'
                ' home.',
    long_description=long_description,
    author='Ben Christenson',
    author_email='Python@BenChristenson.com',
    url='https://github.com/SeabornGames/SeabornGlowforge',
    install_requires=[
        'seaborn_table'
    ],
    extras_require={
    },
    packages=['seaborn_glowforge'],
    license='MIT License',
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5'),
    entry_points={
        'console_scripts': [
            'diagram = seaborn_glowforge.diagram:main',
            'glowforge = seaborn_glowforge.glowforge:main',
        ],
    },
)
