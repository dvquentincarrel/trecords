set --local prog_name trecords
complete -c $prog_name -f
complete -c $prog_name -s c -l config-file -d 'Path to the confilg file'
complete -c $prog_name -s h -l help -d 'Prints help message'
complete -c $prog_name -s f -l filter --no-files -ra "year month week day hour all" -d 'Which entries to consider'
complete -c $prog_name -s d -l database -d "Specific database to use"
complete -c $prog_name -s m -l moment -d "Specific moment to use instead of now"
complete -c $prog_name -s v -l version -d "Print version"
complete -c $prog_name -s j -l json -d "Output data in JSON"
complete -c $prog_name -a add -d "Add a new entry. Default action"
complete -c $prog_name -a edit -d "Edit entries matching the filter"
complete -c $prog_name -a see -d "See entries matching the filter"
complete -c $prog_name -a sum -d "Print time spent for each activity for the entries matching the filter"
complete -c $prog_name -a debug -d "Load the code and data, then drop into a pdb"
complete -c $prog_name -a report -d "WIP"
