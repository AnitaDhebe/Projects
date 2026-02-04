import pytest
import math
import random

# === Passing Tests ===
def test_addition_1(): assert 1 + 1 == 2
def test_subtraction_2(): assert 5 - 3 == 2
def test_multiplication_3(): assert 3 * 3 == 9
def test_division_4(): assert 8 / 2 == 4
def test_modulo_5(): assert 10 % 3 == 1
def test_power_6(): assert 2 ** 3 == 8
def test_fstring_7(): assert f"Hello {'World'}" == "Hello World"
def test_string_concat_8(): assert "py" + "thon" == "python"
def test_list_length_9(): assert len([1, 2, 3]) == 3
def test_tuple_check_10(): assert isinstance((1, 2), tuple)

# === Failing Tests ===
def test_fail_11(): assert 1 == 2
def test_fail_12(): assert "a" in "bcd"
def test_fail_13(): assert 100 < 50
def test_fail_14(): assert not True
def test_fail_15(): assert isinstance("abc", int)
def test_fail_16(): assert len("abc") == 5
def test_fail_17(): assert 5 != 5
def test_fail_18(): assert sum([1, 2, 3]) == 10
def test_fail_19(): assert math.sqrt(16) == 5
def test_fail_20(): assert 3.14 == 3.14159

# === Skipped Tests ===
@pytest.mark.skip(reason="Demo skip 21")
def test_skip_21(): assert True

@pytest.mark.skip(reason="Demo skip 22")
def test_skip_22(): assert False

@pytest.mark.skip(reason="Demo skip 23")
def test_skip_23(): assert 1 / 0

@pytest.mark.skip(reason="Demo skip 24")
def test_skip_24(): raise Exception("Skipping anyway")

@pytest.mark.skip(reason="Demo skip 25")
def test_skip_25(): assert "skip"

# === Error/Exception Tests ===
def test_error_26(): raise ValueError("Intentional error")
def test_error_27(): 1 / 0
def test_error_28(): undefined_variable
def test_error_29(): raise RuntimeError("Runtime issue")
def test_error_30(): open("nonexistent_file.txt")

# === More Mixed Functional/Logic Tests ===
def test_upper_31(): assert "abc".upper() == "ABC"
def test_lower_32(): assert "ABC".lower() == "abc"
def test_title_33(): assert "hello world".title() == "Hello World"
def test_split_34(): assert "a,b,c".split(",") == ["a", "b", "c"]
def test_strip_35(): assert "  hello ".strip() == "hello"
def test_isdigit_36(): assert "123".isdigit()
def test_replace_37(): assert "aabb".replace("a", "") == "bb"
def test_count_38(): assert "banana".count("a") == 3
def test_find_39(): assert "test".find("e") == 1
def test_index_40(): assert [10, 20, 30].index(20) == 1

# === List and Dict Checks ===
def test_dict_key_41(): assert "x" in {"x": 1, "y": 2}
def test_list_append_42(): l = []; l.append(1); assert l == [1]
def test_set_uniqueness_43(): assert len(set([1,1,1,2])) == 2
def test_dict_get_44(): d = {"a": 1}; assert d.get("a") == 1
def test_dict_fail_45(): d = {}; assert d.get("missing") == 1
def test_list_sort_46(): l = [3,1,2]; l.sort(); assert l == [1,2,3]
def test_reversed_47(): assert list(reversed([1, 2])) == [2, 1]
def test_range_48(): assert list(range(3)) == [0, 1, 2]
def test_zip_49(): assert list(zip([1,2], [3,4])) == [(1,3), (2,4)]
def test_enumerate_50(): assert list(enumerate(["a", "b"])) == [(0, "a"), (1, "b")]

# === Boolean Logic ===
def test_bool_51(): assert bool("non-empty")
def test_and_52(): assert True and True
def test_or_53(): assert False or True
def test_not_54(): assert not False
def test_xor_55(): assert True ^ False
def test_chain_bool_56(): assert (1 < 2 and 2 < 3)
def test_in_57(): assert 2 in [1,2,3]
def test_not_in_58(): assert "z" not in "hello"
def test_is_59(): a = b = 10; assert a is b
def test_is_not_60(): assert [] is not []

# === Math and Number Tests ===
def test_abs_61(): assert abs(-5) == 5
def test_round_62(): assert round(3.1459, 2) == 3.15
def test_min_63(): assert min(1, 2, 3) == 1
def test_max_64(): assert max([10, 20]) == 20
def test_pow_65(): assert pow(2, 4) == 16
def test_float_compare_66(): assert abs(0.1 + 0.2 - 0.3) < 1e-9
def test_negative_67(): assert -10 < 0
def test_int_68(): assert int("5") == 5
def test_float_69(): assert float("3.14") == 3.14
def test_divmod_70(): assert divmod(8, 3) == (2, 2)

# === Edge Cases ===
def test_empty_string_71(): assert "" == ""
def test_empty_list_72(): assert [] == []
def test_none_73(): assert None is None
def test_zero_74(): assert 0 == 0
def test_false_75(): assert not False
def test_nan_compare_76(): import math; assert math.isnan(float('nan'))
def test_inf_compare_77(): import math; assert math.isinf(float('inf'))
def test_char_78(): assert ord('A') == 65
def test_chr_79(): assert chr(66) == 'B'
def test_assert_true_80(): assert True

# === More Complex Logic ===
def test_factorial_81(): from math import factorial; assert factorial(5) == 120
def test_even_82(): assert 4 % 2 == 0
def test_odd_83(): assert 5 % 2 == 1
def test_prime_84(): assert all(7 % i != 0 for i in range(2, 7))
def test_fib_85(): fib = [0, 1]; [fib.append(fib[-1]+fib[-2]) for _ in range(8)]; assert fib[5] == 5
def test_palindrome_86(): assert "madam" == "madam"[::-1]
def test_anagram_87(): assert sorted("listen") == sorted("silent")
def test_unique_88(): assert len(set("hello")) != len("hello")
def test_substring_89(): assert "ell" in "hello"
def test_strip_digits_90(): assert "123abc".lstrip("123") == "abc"

# === More Errors and Skips ===
def test_key_error_91(): d = {}; d["x"]
def test_index_error_92(): l = []; l[1]
def test_type_error_93(): '2' + 2
def test_attribute_error_94(): [].not_a_function()
def test_import_error_95(): import nonexisting
@pytest.mark.skip(reason="final skip 96")
def test_skip_96(): assert False
@pytest.mark.skip(reason="final skip 97")
def test_skip_97(): assert True
def test_zero_division_98(): _ = 1 / 0
def test_assert_error_99(): assert False, "Manual assert"
def test_pass_100(): pass

# Test case 1
@pytest.mark.parametrize("i", [1])
def test_fail_once(i):
    assert random.random() < 0.5  # Fails first time (50% chance)

# Test case 2
@pytest.mark.parametrize("i", [2])
def test_fail_once_2(i):
    assert random.random() < 0.5  # Fails first time (50% chance)

# Test case 3
@pytest.mark.parametrize("i", [3])
def test_fail_once_3(i):
    assert random.random() < 0.5  # Fails first time (50% chance)

# Test case 4
@pytest.mark.parametrize("i", [4])
def test_fail_once_4(i):
    assert random.random() < 0.5  # Fails first time (50% chance)

# Test case 5
@pytest.mark.parametrize("i", [5])
def test_fail_once_5(i):
    assert random.random() < 0.5  # Fails first time (50% chance)
