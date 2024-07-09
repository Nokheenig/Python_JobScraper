import os
from enum import Enum

class Platform(Enum):
    indeedFR = "fr.indeed.com"
    linkedInCAN = "www.linkedin.com"


ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
CONFIG_PATH = os.path.join(ROOT_DIR, 'configuration.conf')  # requires `import os`
COUNTRY_CODES_MAP = {
    "FR": "France",
    "CAN": "Canada",
    "KR": "Korea",
    "JP": "Japan",
    "TW": "Taiwan",
    "VN": "Vietnam",
    "PH": "Philippines",
    "TH": "Thailand",
    "IDN": "Indonesia",
    "AUS": "Australia",
    "US": "United-States",
    "UK": "United-Kingdom",
}
CONTRACT_TYPES_BY_COUNTRY_CODE = {
    "FR":{
        "fullTime": ["cdi", "temps-plein", "temps plein", "cdi, temps plein", "cdi, statut cadre"],
        "temporary": ["cdd", "temps plein, cdd"],
        "partTime": ["temps-partiel", "temps partiel"],
        "internship": ["stage", "temps plein, stage"],
        "apprenticeship": ["alternance", "temps plein, alternance", "contrat d'apprentissage", "alternance, contrat d'apprentissage", ""],
        "freelance": ["freelance", "temps plein, indépendant / freelance", "indépendant / freelance"]
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
            "query": {"else": "Île-de-France"}
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
            "query": {"else": "Montreal, QC"}
        },
        {
            "city": "Ottawa",
            "district": "Ontario",
            "query": {"else": "Ottawa, ON"}
        },
        {
            "city": "Toronto",
            "district": "Ontario",
            "query": {"else": "Toronto, ON"}
        },
        {
            "city": "Vancouver",
            "district": "British Columbia",
            "query": {"else": "Vancouver, BC"}
        }
    ],
    "KR": [
        {
            "city": "Seoul",
            "district": "",
            "query": None
        },
    ],
    "JP": [
        {
            "city": "Tokyo",
            "district": "",
            "query": None
        },
        {
            "city": "Osaka",
            "district": "",
            "query": None
        },
        {
            "city": "Kyoto",
            "district": "",
            "query": None
        },
        {
            "city": "Nagoya",
            "district": "",
            "query": None
        },
    ],
    "TW": [
        {
            "city": "Taipei",
            "district": "",
            "query": None
        },
        {
            "city": "Hsinchu",
            "district": "",
            "query": None
        },
    ],
    "VN": [
        {
            "city": "Ho Chi Minh",
            "district": "None",
            "query": None
        },
        {
            "city": "Hanoi",
            "district": "None",
            "query": None
        },
        #{
        #    "city": "Hue",
        #    "district": "None",
        #    "query": None
        #},
        #{
        #    "city": "Da Nang",
        #    "district": "None",
        #    "query": None
        #}
    ],
    "PH": [
        {
            "city": "Manila",
            "district": "None",
            "query": None
        },
        {
            "city": "Taguig",
            "district": "None",
            "query": None
        },
        {
            "city": "Makati",
            "district": "None",
            "query": None
        },
        {
            "city": "Cebu",
            "district": "None",
            "query": None
        },
        {
            "city": "Davao",
            "district": "None",
            "query": None
        }
    ],
    "TH": [
        {
            "city": "Bangkok",
            "district": "None",
            "query": None
        },
    ],
    "IDN": [
        {
            "city": "Jakarata",
            "district": "None",
            "query": None
        },
        {
            "city": "Bandung",
            "district": "None",
            "query": None
        },
    ],
    "AUS": [
        {
            "city": "Sydney",
            "district": "None",
            "query": None
        },
        {
            "city": "Melbourne",
            "district": "None",
            "query": None
        },
        {
            "city": "Brisbane",
            "district": "None",
            "query": None
        },
        {
            "city": "Perth",
            "district": "None",
            "query": None
        }
    ],
    "US": [
        {
            "city": "Phoenix",
            "district": "None",
            "query": None
        },
        {
            "city": "Seattle",
            "district": "None",
            "query": None
        },
        {
            "city": "Austin",
            "district": "None",
            "query": None
        },
        {
            "city": "Portland",
            "district": "None",
            "query": None
        },
        {
            "city": "Los Angeles",
            "district": "None",
            "query": None
        }
    ],
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