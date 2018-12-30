"""Tests for the maker module.
"""
import ast
import sys

import pytest

from mutatest.maker import (
    MutantTrialResult,
    create_mutant,
    get_mutation_targets,
    write_mutant_cache_file,
)
from mutatest.transformers import LocIndex, get_ast_from_src


@pytest.fixture
def add_five_to_mult_mutant(binop_file):
    """Mutant that takes add_five op ADD to MULT"""
    tree = get_ast_from_src(binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = create_mutant(
        tree=tree, src_file=binop_file, target_idx=target_idx, mutation_op=mutation_op
    )
    return mutant


def test_get_mutation_targets(binop_file):
    """Test mutation target retrieval from the bin_op test fixture."""
    tree = get_ast_from_src(binop_file)
    targets = get_mutation_targets(tree)

    assert len(targets) == 4

    expected = {
        LocIndex(ast_class="BinOp", lineno=6, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=6, col_offset=18, op_type=ast.Sub),
        LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add),
        LocIndex(ast_class="BinOp", lineno=15, col_offset=11, op_type=ast.Div),
    }

    assert targets == expected


def test_create_mutant(binop_file, stdoutIO):
    """Basic mutant creation to modify the add_five() function from add to mult."""
    tree = get_ast_from_src(binop_file)

    # this target is the add_five() function, changing add to mult
    target_idx = LocIndex(ast_class="BinOp", lineno=10, col_offset=11, op_type=ast.Add)
    mutation_op = ast.Mult

    mutant = create_mutant(
        tree=tree, src_file=binop_file, target_idx=target_idx, mutation_op=mutation_op
    )

    # uses the redirection for stdout to capture the value from the final output of binop_file
    with stdoutIO() as s:
        exec(mutant.mutant_code)
        assert int(s.getvalue()) == 25

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    assert mutant.src_file == binop_file
    assert mutant.cfile == expected_cfile
    assert mutant.src_idx == target_idx


def test_write_mutant_cache_file(add_five_to_mult_mutant, binop_file):
    """Test writing the cache file out to the temp directory with the mutation."""

    tag = sys.implementation.cache_tag
    expected_cfile = binop_file.parent / "__pycache__" / ".".join([binop_file.stem, tag, "pyc"])

    write_mutant_cache_file(add_five_to_mult_mutant)

    assert expected_cfile.exists()


@pytest.mark.parametrize(
    "returncode, expected_status", [(0, "SURVIVED"), (1, "DETECTED"), (2, "ERROR"), (3, "UNKNOWN")]
)
def test_MutantTrialResult(returncode, expected_status, add_five_to_mult_mutant):
    """Test that the status property translates as expected from return-codes."""
    trial = MutantTrialResult(add_five_to_mult_mutant, returncode)
    assert trial.status == expected_status