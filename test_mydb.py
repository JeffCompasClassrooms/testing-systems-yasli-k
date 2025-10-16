import pytest
import os
import pickle
import tempfile
from mydb import MyDB


@pytest.fixture
def temp_db_file():
    # Create a temporary file and initialize with pickled empty list
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_file = tmp.name
        # Write an empty list to ensure valid pickle data
        with open(db_file, 'wb') as f:
            pickle.dump([], f)
    yield db_file
    # Tear down: Remove the file after each test
    if os.path.exists(db_file):
        os.remove(db_file)


def describe_mydb():
    def describe_init():
        def it_creates_empty_file_if_not_exists():
            # Create a non-existing file path
            temp_dir = tempfile.gettempdir()
            db_file = os.path.join(temp_dir, 'test_mydb.db')
            if os.path.exists(db_file):
                os.remove(db_file)
            db = MyDB(db_file)
            assert os.path.isfile(db_file) is True
            with open(db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == []

        def it_does_not_overwrite_existing_file(temp_db_file):
            # Pre-write a file with data
            with open(temp_db_file, 'wb') as f:
                pickle.dump(['existing'], f)
            db = MyDB(temp_db_file)
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['existing']

    def describe_save_strings():
        def it_saves_empty_list(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveStrings([])
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == []

        def it_saves_non_empty_list(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveStrings(['a', 'b'])
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['a', 'b']

        def it_overwrites_existing_content(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveStrings(['old'])
            db.saveStrings(['new'])
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['new']

    def describe_load_strings():
        def it_loads_empty_list_from_empty_file(temp_db_file):
            db = MyDB(temp_db_file)
            result = db.loadStrings()
            assert result == []

        def it_loads_existing_list(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveStrings(['x', 'y'])
            result = db.loadStrings()
            assert result == ['x', 'y']

    def describe_save_string():
        def it_appends_to_empty_file(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveString('test')
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['test']

        def it_appends_to_existing_list(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveStrings(['a'])
            db.saveString('b')
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['a', 'b']

        def it_appends_multiple_strings(temp_db_file):
            db = MyDB(temp_db_file)
            db.saveString('first')
            db.saveString('second')
            with open(temp_db_file, 'rb') as f:
                data = pickle.load(f)
            assert data == ['first', 'second']