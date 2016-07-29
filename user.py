"""
This module represents a user from the database
"""
from json import dumps

class User(object):
    def __init__(self, columns, values):
      """
      Set the initial attributes of this user object

      Args:
          input: the results of a `SELECT *` query on the user table
      """
      for i in range(len(values)):
          setattr(self, columns[i][0], values[i])

      setattr(self, "json", dumps(self.__dict__))