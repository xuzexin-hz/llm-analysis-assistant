# __main__.py
import importlib.metadata
import os

from llm_analysis_assistant.server import main

if __name__ == '__main__':
    os.environ["PROJECT_NAME"] = __package__
    try:
        version = importlib.metadata.version("llm_analysis_assistant")
        os.environ["PROJECT_VERSION"] = 'v' + version
    except importlib.metadata.PackageNotFoundError:
        pass
    main()
