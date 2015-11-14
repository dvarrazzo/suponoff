from setuptools import setup, find_packages
from suponoff import __version__ as version


if __name__ == '__main__':
    with open("README.rst") as f:
        long_description = f.read()
    setup(
        name="suponoff",
        version=version,
        author="Gambit Research",
        author_email="opensource@gambitresearch.com",
        description="An alternative Supervisor web interface.",
        long_description=long_description,
        license="BSD",
        url="https://github.com/GambitResearch/suponoff",
        zip_safe=False,
        include_package_data=True,
        packages=find_packages(),
        scripts=[
            'suponoff-monhelper.py'
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment",
            "Framework :: Django",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.3",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            "Topic :: Internet :: WWW/HTTP :: WSGI",
            ("Topic :: Software Development :: Libraries :: "
             "Application Frameworks"),
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Systems Administration",

        ])
