import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
      name='dmtools',
      version='0.1',
      description='Tools for Data managers to Assess datasets, codelists etc.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/GSS-Cogs/dm_tools',
      author='Leigh Perryman',
      author_email='leigh.perryman@gsscogs.uk',
      license='MIT',
      packages=setuptools.find_packages(),
      zip_safe=False)
