# 0.3
- moment cli flag handles new formats:
  - YYYY-MM-DD (implies 00:00:00)
  - MM-DD (implies current year, 00:00:00)
  - hh:mm:ss (implies today)
  - hh:mm (implies today, 00 seconds)
# 0.2
- Edit command, outputs the rows returned by the current filter as a json file to be edited, then inserted back into the DB
- Json output of entries and sums, with the --json flag
# 0.1
First release. CLI interface only, arguably lacks a bit of QoL regarding edition (compared to previous solution at least)
