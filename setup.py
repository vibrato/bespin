from setuptools import setup, find_packages
from bespin import VERSION

setup(
      name = "bespin"
    , version = VERSION
    , packages = ['bespin'] + ['bespin.%s' % pkg for pkg in find_packages('bespin')]
    , include_package_data = True

    , dependency_links = ["git+https://github.com/delfick/pyrelic.git@0.7.3#egg=pyrelic-0.7.3"]

    , install_requires =
      [ "delfick_error==1.6.1"
      , "option_merge==0.9.6"
      , "input_algorithms==0.4.4.4"

      , "six"
      , "pytz"
      , "slacker"
      , "humanize"
      , "argparse"
      , "requests"
      , "paramiko"

      , "radssh==1.0.1"
      , "pyrelic==0.7.3"
      , "boto==2.38.0"
      , "pyYaml==3.10"
      , "ultra_rest_client==0.1.4"
      , "rainbow_logging_handler==2.2.2"
      , "FileChunkIO==1.6"
      ]

    , extras_require =
      { "tests":
        [ "noseOfYeti>=1.5.0"
        , "nose"
        , "mock"
        , "moto"

        # Need to ensure httpretty is not 0.8.7
        # To prevent an infinite loop in python3 tests
        , "httpretty==0.8.6"
        ]
      }

    , entry_points =
      { 'console_scripts' :
        [ 'bespin = bespin.executor:main'
        ]
      }

    # metadata for upload to PyPI
    , url = "https://github.com/realestate-com-au/bespin"
    , author = "Stephen Moore"
    , author_email = "stephen.moore@rea-group.com"
    , description = "Opinionated wrapper around boto that reads yaml"
    , license = "MIT"
    , keywords = "cloudformation boto"
    )

