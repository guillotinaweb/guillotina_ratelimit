from setuptools import find_packages
from setuptools import setup


try:
    README = open('README.rst').read()
except IOError:
    README = None

setup(
    name='guillotina_ratelimit',
    version='1.0.0.dev0',
    description='Provide global and service rate limiting in a per user basis',
    long_description=README,
    install_requires=[
        'guillotina>=4.3.5.dev0',
        'guillotina_rediscache>=2.1.0'
    ],
    author='Ferran Llamas',
    author_email='llamas.arroniz@gmai.com',
    url='https://github.com/guillotinaweb/guillotina_ratelimit',
    packages=find_packages(exclude=['demo']),
    include_package_data=True,
    tests_require=[
        'pytest'
    ],
    extras_require={
        'test': [
            'pytest',
            'docker',
            'psycopg2',
            'pytest-asyncio',
            'pytest-aiohttp',
            'pytest-cov',
            'coverage',
            'pytest-docker-fixtures',
        ]
    },
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
        'Intended Audience :: Developers',
    ],
    entry_points={
    }
)
