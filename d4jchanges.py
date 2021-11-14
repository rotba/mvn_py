import sys
from Repo import Repo

if __name__ == '__main__':
    repo = Repo(sys.argv[1])
    repo.set_compiler_version()