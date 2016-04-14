import os
import sys

from setuptools import setup, find_packages

sys.path.insert(0, os.path.dirname(__file__))
config = __import__('config')


def run():
    meta = dict(
        name='pulsar-odm',
        author="Luca Sbardella",
        author_email="luca@quantmind.com",
        url="https://github.com/quantmind/pulsar-odm",
        zip_safe=False,
        license='BSD',
        long_description=config.read('README.rst'),
        packages=find_packages(include=('odm', 'odm.*')),
        setup_requires=['pulsar'],
        install_requires=config.requirements('requirements.txt')[0],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.4',
            'Topic :: Utilities'])

    setup(**config.setup(meta, 'odm'))


if __name__ == '__main__':
    run()
