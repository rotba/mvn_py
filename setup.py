from setuptools import setup, find_packages

install_requires = ['javalang', 'enum']

setup(
    name='mvnpy',
    version='1.0.1',
    packages=find_packages(),
    url='https://github.com/rotba/mvnpy',
    license='',
    author='Rotem Barak',
    author_email='rotba@post.bgu.ac.il',
    install_requires=install_requires,
    description='Python Distribution Utilities'
)
