import imp
import inspect
import sys
import re

from behave import step


def define_steps(package_regex, step_module, translations):
    class BehaveStepCollectionLoader:
        def __init__(self, translation):
            self.translation = translation

        def load_module(self, fullname):
            try:
                return sys.modules[fullname]
            except KeyError:
                pass

            module = imp.new_module(fullname)
            module.__file__ = step_module.__file__
            module.__doc__ = step_module.__doc__
            module.__path__ = []
            module.__loader__ = self

            members = inspect.getmembers(step_module, inspect.isfunction)
            for name, value in members:
                if name.startswith('_'):  # Private function
                    continue
                for text in reversed(self.translation[name]):
                    value = step(text)(value)
                setattr(module, name, value)

            sys.modules.setdefault(fullname, module)
            return module


    class BehaveStepCollectionFinder:
        module_pattern = re.compile(package_regex)

        def find_module(self, fullname, path=None):
            match = self.module_pattern.match(fullname) 
            if match:
                request_lang = match.group("lang")
                try:
                    translation = translations[request_lang]
                except KeyError:
                    return None
                else:
                    return BehaveStepCollectionLoader(translation)
            else:
                return None

    # Append the step finder to sys.meta_path
    sys.meta_path.append(BehaveStepCollectionFinder())
