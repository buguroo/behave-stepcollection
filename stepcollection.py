import imp
import inspect
import re
import sys
import types

from behave import step as step_decorator

from substeps import SubSteps


def define_steps(package_regex, step_module, translations, substeps=False):
    class BehaveStepCollectionLoader:
        def __init__(self, language, translation):
            self.language = language
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
            if substeps:
                module.substeps = SubSteps(language=self.language)
                step_decorator = module.substeps.step
            module.LANG = self.language

            members = inspect.getmembers(step_module, inspect.isfunction)
            for name, value in members:
                if name.startswith('_'):  # Private function
                    continue

                # Copy the function adding custom globals
                new_globals = value.__globals__.copy()
                new_globals['__language__'] = self.language

                function_copy = types.FunctionType(
                    value.__code__,
                    new_globals,
                    value.__name__,
                    value.__defaults__,
                    value.__closure__)

                for text in reversed(self.translation[name]):
                    value = step_decorator(text)(function_copy)

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
                    return BehaveStepCollectionLoader(request_lang,
                                                      translation)
            else:
                return None

    # Append the step finder to sys.meta_path
    sys.meta_path.append(BehaveStepCollectionFinder())
