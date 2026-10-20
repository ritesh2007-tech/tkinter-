"""
Serial Letter and Serial Number Management Service.
Specification:
- Serial letter: A to Z
- Serial no: 1 to 9999 per letter
- 1 Serial Letter has 100 Books, each Book has 100 Entries (10,000 capacity)
- Calculates Book No and Entry No automatically
"""
import math
from config import SERIAL_LETTERS, MAX_SERIAL_PER_LETTER, ENTRIES_PER_BOOK, BOOKS_PER_LETTER
from database.models import PledgeDAO, SettingsDAO

class SerialService:
    @staticmethod
    def calculate_book_and_entry(serial_no):
        """
        Given serial_no (1-9999):
        Book 1: entries 1 to 100
        Book 2: entries 101 to 200
        ...
        Book 100: entries 9901 to 10000
        """
        try:
            s_no = int(serial_no)
            if s_no <= 0:
                s_no = 1
            book_no = math.ceil(s_no / float(ENTRIES_PER_BOOK))
            entry_no = ((s_no - 1) % ENTRIES_PER_BOOK) + 1
            return book_no, entry_no
        except Exception:
            return 1, 1

    @staticmethod
    def get_current_or_next_serial(letter=None):
        """
        Retrieves next serial number for specified letter or current active letter in settings.
        """
        if not letter:
            letter = SettingsDAO.get("current_serial_letter", "A")
        
        letter = letter.upper()
        info = PledgeDAO.get_next_serial_info(letter)
        return info

    @staticmethod
    def advance_to_next_letter_if_full(current_letter, current_serial_no):
        """
        If current letter reached 9999, advances to next letter in A-Z.
        """
        if current_serial_no >= MAX_SERIAL_PER_LETTER:
            curr_idx = SERIAL_LETTERS.index(current_letter) if current_letter in SERIAL_LETTERS else 0
            if curr_idx < len(SERIAL_LETTERS) - 1:
                next_letter = SERIAL_LETTERS[curr_idx + 1]
                SettingsDAO.set("current_serial_letter", next_letter)
                return next_letter
        return current_letter

    @staticmethod
    def validate_serial(letter, number, exclude_pledge_id=None):
        """Validates if serial is valid and not already taken."""
        letter = str(letter).strip().upper()
        if letter not in SERIAL_LETTERS:
            return False, f"Invalid Serial Letter '{letter}'. Must be between A and Z."
        
        try:
            num = int(number)
            if num < 1 or num > MAX_SERIAL_PER_LETTER:
                return False, f"Serial Number must be between 1 and {MAX_SERIAL_PER_LETTER}."
        except ValueError:
            return False, "Serial Number must be a positive integer."

        if PledgeDAO.is_serial_taken(letter, num, exclude_pledge_id):
            return False, f"Pledge Number {letter}-{num:04d} is already allocated!"

        return True, "Valid"
