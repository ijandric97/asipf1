import sqlite3

DATA_FOLDER_PATH = "data"
DATABASE_FILE_PATH = DATA_FOLDER_PATH + "/f1db.sqlite"

con = sqlite3.connect(DATABASE_FILE_PATH)
