from main import RecordTable
from orm import FancyRow

def main(table: RecordTable, values: list[FancyRow]):
    """Opens editor to edit values of the given rows"""
    table.edit(values)
