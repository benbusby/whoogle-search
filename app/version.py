import os

optional_dev_tag = '-update-testing'
if os.getenv('DEV_BUILD'):
    optional_dev_tag = '.dev' + os.getenv('DEV_BUILD')

__version__ = '1.2.0' + optional_dev_tag

