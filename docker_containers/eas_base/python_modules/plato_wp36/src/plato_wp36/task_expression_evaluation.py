# -*- coding: utf-8 -*-
# task_expression_evaluation.py

"""
A class which takes the data structure containing the job description for a task, and evaluates any expressions
within that data structure. Where parameter values are specified as strings starting with the characters ' " or (
these are taken as mathematical expressions to be evaluated in an environment where constants and metadata values
are available.
"""

# noinspection PyUnresolvedReferences
import random

from typing import Any, Optional, Dict

import plato_wp36.constants


class TaskExpressionEvaluation:
    """
    A class which takes the data structure containing the job description for a task, and evaluates any expressions
    within that data structure. Where parameter values are specified as strings starting with the characters ' " or (
    these are taken as mathematical expressions to be evaluated in an environment where constants and metadata values
    are available.
    """

    def __init__(self, metadata: Optional[Dict] = None):
        """
        Create a new expression evaluator.

        :param metadata:
            A dictionary of all the metadata which is available in the current context.
        :type metadata:
            Optional[Dict]
        """

        # Store the currently-available metadata
        self.metadata = metadata

    def evaluate_expression(self, expression: Any):
        """
        Evaluate an expression in the current context.

        :param expression:
            The expression to evaluate
        :return:
            The expression value
        """

        # If expression is not a string, treat it as a literal value
        if not isinstance(expression, str):
            return expression

        # If the expression does not begin with quotes or brackets, treat it as a literal value
        expression = expression.strip()
        if (len(expression) == 0) or (expression[0] not in "\'\"("):
            return expression

        # Prepare local variables which may be used in the expression
        # noinspection PyUnusedLocal
        constants = plato_wp36.constants.EASConstants()
        # noinspection PyUnusedLocal
        metadata = {keyword: value.value for keyword, value in self.metadata.items()}

        # Evaluate expression
        return eval(expression)

    def evaluate_in_structure(self, structure: Any):
        """
        Cycle through all the items in a hierarchy of lists and dictionaries, evaluating all the items.

        :param structure:
            The structure of lists and dictionaries to cycle through.
        :return:
            A copy of the structure in which all expressions have been evaluated.
        """

        # If we are processing a dictionary, evaluate expressions in any of its entries in turn
        if isinstance(structure, dict):
            output = {}
            for keyword_raw, value_raw in structure.items():
                # Even the dictionary keys can contain expressions we need to evaluate
                keyword = self.evaluate_in_structure(structure=keyword_raw)
                # Special case for nested 'taskList' entries, which contain child subprocesses, which may need
                # metadata we don't have yet. So don't evaluate expressions within them at this time.
                if keyword == 'task_list':
                    output[keyword] = value_raw
                # In all other cases, evaluate nested levels immediately
                else:
                    output[keyword] = self.evaluate_in_structure(structure=value_raw)
            return output

        # If we are processing a list, evaluate expressions in any of its entries in turn
        if isinstance(structure, (list, tuple)):
            return [self.evaluate_in_structure(structure=value) for value in structure]

        # Strings and numbers we simply evaluate straight away
        return self.evaluate_expression(expression=structure)
