import os
import setuptools

optional_dev_tag = ''
if os.getenv('DEV_BUILD'):
    optional_dev_tag = '.dev' + os.getenv('DEV_BUILD')

setuptools.setup(version='0.8.0' + optional_dev_tag)
