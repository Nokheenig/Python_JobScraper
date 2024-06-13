import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
CONFIG_PATH = os.path.join(ROOT_DIR, 'configuration.conf')  # requires `import os`
COUNTRY_CODES_MAP = {
    "FR": "France",
    "CAN": "Canada",
    "KR": "Korea"
}
CONTRACT_TYPES_BY_COUNTRY_CODE = {
    "FR":{
        "fullTime": ["cdi", "temps-plein", "temps plein"],
        "temporary": ["cdd"],
        "partTime": ["temps-partiel", "temps partiel"],
        "internship": ["stage"],
        "apprenticeship": ["alternance"],
        "freelance": ["freelance"]
    },
    "else":{
        "fullTime": ["fulltime","full-time", "full time"],
        "temporary": ["contract", "temporary"],
        "partTime": ["part-time", "part time"],
        "internship": ["internship"],
        "apprenticeship": ["apprenticeship","co-op", "co op"],
        "freelance": ["freelance"]
    },
}
JOB_SEARCH_LOCATIONS = {
    "FR": [
        {
            "city": "Paris",
            "district": "Ile de France",
            "query": "Île-de-France"
        },
        {
            "city": "Lyon",
            "district": "Auv. Rhone-Alpes",
            "query": None
        }
    ],
    "CAN": [
        {
            "city": "Montreal",
            "district": "Quebec",
            "query": "Montreal, QC"
        },
        {
            "city": "Ottawa",
            "district": "Ontario",
            "query": "Ottawa, ON"
        },
        {
            "city": "Toronto",
            "district": "Ontario",
            "query": "Toronto, ON"
        },
        {
            "city": "Vancouver",
            "district": "British Columbia",
            "query": "Vancouver, BC"
        }
    ],
    "KR": "Korea"
}
"""
You can do this how Django does it: define a variable to the Project Root from a file that is in the top-level of the project. For example, if this is what your project structure looks like:

project/
    configuration.conf
    definitions.py
    main.py
    utils.py
In definitions.py you can define (this requires import os):

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
Thus, with the Project Root known, you can create a variable that points to the location of the configuration (this can be defined anywhere, but a logical place would be to put it in a location where constants are defined - e.g. definitions.py):

CONFIG_PATH = os.path.join(ROOT_DIR, 'configuration.conf')  # requires `import os`
Then, you can easily access the constant (in any of the other files) with the import statement (e.g. in utils.py): from definitions import CONFIG_PATH.
"""