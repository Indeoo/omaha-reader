# main.py
from src.core.service.moves_by_street import group_moves_by_street, group_moves_by_street_simple

if __name__ == "__main__":
    # Test data 1: Standard game with multiple betting rounds
    test_data_1 = {
        1: ["call", "call", "check", "check"],
        2: ["fold"],
        3: ["raise", "bet", "bet", "bet"],
        4: ["call", "raise", "raise", "call"],
        5: ["fold"],
        6: ["call", "call", "call", "fold"]
    }

    # Test data 2: Game with extensive preflop action
    test_data_2 = {
        1: ["raise", "raise", "call"],  # 3-bet, 5-bet, call 6-bet
        2: ["fold"],
        3: ["raise", "raise", "raise"],  # Open, 4-bet, 6-bet
        4: ["call", "fold"],  # Call open, fold to 3-bet
        5: ["fold"],
        6: ["fold"]
    }

    # Test data 3: Heads-up battle
    test_data_3 = {
        1: ["raise", "call", "bet", "raise", "call", "check", "bet"],
        2: ["fold"],
        3: ["fold"],
        4: ["fold"],
        5: ["fold"],
        6: ["call", "raise", "call", "call", "raise", "raise", "call"]
    }

    # Test data 4: Complex multi-street action
    test_data_4 = {
        1: ["call", "check", "check", "call", "call", "fold"],
        2: ["raise", "bet", "check", "bet", "bet", "bet"],
        3: ["fold"],
        4: ["call", "check", "raise", "raise", "raise", "raise"],
        5: ["fold"],
        6: ["call", "check", "call", "call", "call", "call"]
    }

    # Test data 5: Check-fest
    test_data_5 = {
        1: ["check", "check", "check", "check"],
        2: ["check", "check", "check", "check"],
        3: ["check", "check", "check", "check"],
        4: ["check", "check", "check", "check"],
        5: ["fold"],
        6: ["fold"]
    }

    print("Test 1 - Standard game:")
    result_1 = group_moves_by_street(test_data_1)
    for street, moves in result_1.items():
        print(f"  {street}: {moves}")
    print()

    print("Test 2 - Heavy preflop action:")
    result_2 = group_moves_by_street(test_data_2)
    for street, moves in result_2.items():
        print(f"  {street}: {moves}")
    print()

    print("Test 3 - Heads-up battle:")
    result_3 = group_moves_by_street(test_data_3)
    for street, moves in result_3.items():
        print(f"  {street}: {moves}")
    print()

    print("Test 4 - Complex multi-street:")
    result_4 = group_moves_by_street(test_data_4)
    for street, moves in result_4.items():
        print(f"  {street}: {moves}")
    print()

    print("Test 5 - Check-fest:")
    result_5 = group_moves_by_street(test_data_5)
    for street, moves in result_5.items():
        print(f"  {street}: {moves}")

    # Test simple approach
    print("\n=== Simple Approach ===")
    print("Test 1 - Standard game:")
    result_1_simple = group_moves_by_street_simple(test_data_1)
    for street, moves in result_1_simple.items():
        print(f"  {street}: {moves}")