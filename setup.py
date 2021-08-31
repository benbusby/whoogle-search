import os
import setuptools
import time

long_description = open('README.md', 'r').read()

requirements = list(open('requirements.txt', 'r'))

optional_dev_tag = ''
if os.getenv('DEV_BUILD'):
    optional_dev_tag = '.dev' + str(int(time.time()))

setuptools.setup(
    author='Ben Busby',
    author_email='contact@benbusby.com',
    name='whoogle-search',
    version='0.5.4' + optional_dev_tag,
    include_package_data=True,
    install_requires=requirements,
    description='Self-hosted, ad-free, privacy-respecting metasearch engine',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/benbusby/whoogle-search',
    entry_points={
        'console_scripts': [
            'whoogle-search=app.routes:run_app',
        ]
    },
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
