from main import RecordTable
from config import Config

def main(table: RecordTable, config: Config):
    """Prompts user for informations about and entry to add"""
    table.add_entry(config.moment)
