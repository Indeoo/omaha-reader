# main.py
from src.core.service.moves_by_street import group_moves_by_street, group_moves_by_street_simple

if __name__ == "__main__":
    # Test data 1: Standard game with multiple betting rounds
    test_data_1 = {
        "BTN": ["call", "call", "check", "check"],
        "SB": ["fold"],
        "BB": ["raise", "bet", "bet", "bet"],
        "UTG": ["call", "raise", "raise", "call"],
        "MP": ["fold"],
        "CO": ["call", "call", "call", "fold"]
    }

    # Test data 2: Game with extensive preflop action
    test_data_2 = {
        "BTN": ["raise", "raise", "call"],  # 3-bet, 5-bet, call 6-bet
        "SB": ["fold"],
        "BB": ["raise", "raise", "raise"],  # Open, 4-bet, 6-bet
        "UTG": ["call", "fold"],  # Call open, fold to 3-bet
        "MP": ["fold"],
        "CO": ["fold"]
    }

    # Test data 3: Heads-up battle
    test_data_3 = {
        "BTN": ["raise", "call", "bet", "raise", "call", "check", "bet"],
        "SB": ["fold"],
        "BB": ["fold"],
        "UTG": ["fold"],
        "MP": ["fold"],
        "CO": ["call", "raise", "call", "call", "raise", "raise", "call"]
    }

    # Test data 4: Complex multi-street action
    test_data_4 = {
        "BTN": ["call", "check", "check", "call", "call", "fold"],
        "SB": ["raise", "bet", "check", "bet", "bet", "bet"],
        "BB": ["fold"],
        "UTG": ["call", "check", "raise", "raise", "raise", "raise"],
        "MP": ["fold"],
        "CO": ["call", "check", "call", "call", "call", "call"]
    }

    # Test data 5: Check-fest
    test_data_5 = {
        "BTN": ["check", "check", "check", "check"],
        "SB": ["check", "check", "check", "check"],
        "BB": ["check", "check", "check", "check"],
        "UTG": ["check", "check", "check", "check"],
        "MP": ["fold"],
        "CO": ["fold"]
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