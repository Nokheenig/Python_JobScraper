import re
#from ..definitions import 
class JobRoutines:
    def __init__(self) -> None:
        self.tags = set([
            "kotlin",
            "python",
            "selenium",
            "room",
            "firebase",
            "gson",
            "compose",
            "jetpack compose",
            "retrofit",
            "mvvm",
            "coroutine",
            "flutter",
            "android",
            "html",
            "css",
            "javascript",
            "django",
            "vue.js",
            "vuejs",
            "vue-js",
            "php",
            "flask",
            "sqlalchemy",
            "pymongo",
            "pytest",
            "fastapi",
            "numpy",
            "java",
            "j2e",
            "jee",
            "spring",
            "springboot",
            "nginx",
            "apache",
            "api",
            "openapi",
            "swagger",
            "jwt",
            "json web token",
            "oauth",
            "docker",
            "jenkins",
            "mysql",
            "postgresql",
            "mongodb",
            "sqlite",
            "r",
            "shiny",
            "pandas",
            "matplotlib",
            "jupyter",
            "tensorflow",
            "keras",
            "bash",
            "jira",
            "c",
            "c++",
            "rust",
            "c#",
            ".net",
            "typescript",
            "go",
            "golang",
        ])
        regexCharactersExpr = r"\\|\^|\$|\.|\||\?|\*|\+|\(|\)|\[|\]|\{|\}"
        reCharFinder = re.compile(regexCharactersExpr)

        # Build regex expression to identiffy the tags
        # Escape tags characters used in regular expressions
        matches = []
        tagsStr = "@".join(self.tags)
        for m in reCharFinder.finditer(tagsStr):
            matches.append(m)
        matches.reverse()
        for m in matches: tagsStr = tagsStr[:m.start()] + "\\" + tagsStr[m.start():m.end()] + tagsStr[m.end():]
        #tagsStr = tagsStr.split("@")
        #print(tagsStr)
        #tagsStr = tagsStr.replace()
        tagsRegStr = "|".join([f"\\s+{tag}\\s+" for tag in tagsStr.split("@")])
        print(tagsRegStr)

def applyTags():
    pass

if __name__ == "__main__":
    JobRoutines()