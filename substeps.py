from argparse import Namespace
import contextlib

from behave.parser import Parser
from behave.step_registry import StepRegistry
from behave.step_registry import names as step_names


class SubContext(Namespace):
    @contextlib.contextmanager
    def user_mode(self):
        """To keep Match.run happy."""
        yield


class SubSteps:
    def __init__(self, language=None, variant=None):
        self.parser = Parser(language=language, variant=variant)
        self.registry = StepRegistry()

        # Create decorators for the local registry
        for step_type in step_names.split():
            setattr(self, step_type, self.registry.make_decorator(step_type))

    def run(self, text, context):
        """
        Parse the given text and yield step functions.

        """
        steps = self.parser.parse_steps(text)
        for step in steps:
            match = self.registry.find_match(step)
            if match is None:
                raise ValueError("substep not found '%s'" % step)
            else:
                subcontext = SubContext(
                    table=step.table,
                    text=step.text,
                    step_context=context)
                yield match.run(context)
