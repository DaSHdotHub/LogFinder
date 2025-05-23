# Logfinder
## How to use the script:

1. **Save the script** as `log_finder.py`

2. **Run with a tar file:**
```bash
'Mac'
python3 log_finder.py /path/to/your/archive.tar "search_string"

'Windows'
python log_finder.py /path/to/your/archive.tar "search_string"

```

3. **Run with a directory:**
```bash
'Mac'
python3 log_finder.py /path/to/directory "search_string"

'Windows'
python log_finder.py /path/to/directory "search_string"
```

4. **Specify custom output directory:**
```bash
'Mac'
python3 log_finder.py /path/to/archive.tar "search_string" -o log_results

'Windows'
python log_finder.py /path/to/archive.tar "search_string" -o log_results
```
***

## What the script does:

1. **Extracts the main tar file** (if provided) to a temporary directory
2. **Finds all .tar.gz files** within the extracted content
3. **Extracts each .tar.gz file** to access the nested content
4. **Searches all .log files** for your specified string
5. **Copies matching log files** to an output directory, preserving folder structure
6. **Creates a detailed summary** in `result.txt` showing:
   - Total files searched
   - Number of files with matches
   - Total number of matches
   - For each matching file: filename, number of matches, and line numbers with content



## Output structure:
```
search_results/
├── extracted_logs/          # Log files where matches were found
│   └── [original folder structure preserved]
└── result.txt              # Detailed summary