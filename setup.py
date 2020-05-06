import setuptools

long_description = open('README.md', 'r').read()

requirements = list(open('requirements.txt', 'r'))

setuptools.setup(
    author='Ben Busby',
    author_email='benbusby@protonmail.com',
    name='whoogle-search',
    version='0.1.0',
    scripts=['whoogle-search'],
    include_package_data=True,
    install_requires=requirements,
    description='Self-hosted, ad-free, privacy-respecting alternative to Google search',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/benbusby/whoogle-search',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
