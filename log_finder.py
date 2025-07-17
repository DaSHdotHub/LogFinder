#!/usr/bin/env python3
import os
import tarfile
import tempfile
import shutil
import argparse
import gzip
import re
from pathlib import Path
from typing import List, Tuple, Dict

def extract_tar_file(tar_path: str, extract_to: str) -> None:
    """Extract a tar file to the specified directory."""
    with tarfile.open(tar_path, 'r') as tar:
        tar.extractall(extract_to)

def find_tar_gz_files(directory: str) -> List[str]:
    """Find all .tar.gz files in the given directory."""
    tar_gz_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.tar.gz'):
                tar_gz_files.append(os.path.join(root, file))
    return tar_gz_files

def find_log_files(directory: str) -> List[str]:
    """Find all log files (both compressed and uncompressed) in the given directory."""
    log_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Match uncompressed .log files (but not .log.gz_* files)
            if file.endswith('.log') and not re.match(r'.*\.log\.gz_\d+', file):
                log_files.append(os.path.join(root, file))
            # Match rotated log files (.log_numbers)
            elif re.match(r'.*\.log_\d+$', file):
                log_files.append(os.path.join(root, file))
    return log_files

def find_compressed_log_files(directory: str) -> List[str]:
    """Find all compressed log files (.gz, .log.gz_*) in the given directory."""
    compressed_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Match .gz files (excluding .tar.gz) and .log.gz_* pattern files
            if (file.endswith('.gz') and not file.endswith('.tar.gz')) or \
               re.match(r'.*\.log\.gz_\d+', file):
                compressed_files.append(os.path.join(root, file))
    return compressed_files

def is_compressed_file(file_path: str) -> bool:
    """Check if a file is compressed based on its name."""
    filename = os.path.basename(file_path)
    return filename.endswith('.gz') or re.match(r'.*\.log\.gz_\d+', filename)

def search_in_file(file_path: str, search_string: str) -> List[Tuple[int, str]]:
    """Search for a string in a file and return line numbers and content."""
    matches = []
    try:
        if is_compressed_file(file_path):
            # Handle compressed files
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_string in line:
                        matches.append((line_num, line.strip()))
        else:
            # Handle uncompressed files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_string in line:
                        matches.append((line_num, line.strip()))
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return matches

def copy_matching_files(source_files: List[str], dest_dir: str, temp_dir: str) -> None:
    """Copy files with matches to the destination directory, preserving structure."""
    for file_path in source_files:
        # Create relative path from temp directory
        rel_path = os.path.relpath(file_path, temp_dir)
        dest_path = os.path.join(dest_dir, rel_path)
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(file_path, dest_path)

def main():
    parser = argparse.ArgumentParser(description='Search for strings in log files within nested tar archives')
    parser.add_argument('input_path', help='Path to tar file or directory')
    parser.add_argument('search_string', help='String to search for')
    parser.add_argument('-o', '--output', default='search_results', help='Output directory name (default: search_results)')
    
    args = parser.parse_args()
    
    input_path = args.input_path
    search_string = args.search_string
    output_dir = args.output
    
    # Create output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Create extracted files directory within output
    extracted_dir = os.path.join(output_dir, 'extracted_logs')
    os.makedirs(extracted_dir)
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # Step 1: Handle input (tar file or directory)
        if os.path.isfile(input_path) and input_path.endswith('.tar'):
            print(f"Extracting main tar file: {input_path}")
            extract_tar_file(input_path, temp_dir)
            work_dir = temp_dir
        elif os.path.isdir(input_path):
            work_dir = input_path
        else:
            print(f"Error: {input_path} is not a valid tar file or directory")
            return
        
        # Step 2: Find and extract all .tar.gz files
        print("Searching for .tar.gz files...")
        tar_gz_files = find_tar_gz_files(work_dir)
        print(f"Found {len(tar_gz_files)} .tar.gz files")
        
        extraction_dir = os.path.join(temp_dir, 'extracted_content')
        os.makedirs(extraction_dir, exist_ok=True)
        
        for tar_gz_file in tar_gz_files:
            print(f"Extracting: {os.path.basename(tar_gz_file)}")
            try:
                extract_tar_file(tar_gz_file, extraction_dir)
            except Exception as e:
                print(f"Error extracting {tar_gz_file}: {e}")
        
        # Step 3: Find all log files (both compressed and uncompressed)
        print("Searching for log files...")
        log_files = find_log_files(extraction_dir)
        compressed_log_files = find_compressed_log_files(extraction_dir)
        all_log_files = log_files + compressed_log_files
        
        print(f"Found {len(log_files)} uncompressed log files")
        print(f"Found {len(compressed_log_files)} compressed log files")
        print(f"Total log files: {len(all_log_files)}")
        
        # Step 4: Search for the string in log files
        print(f"Searching for '{search_string}' in log files...")
        results = {}
        files_with_matches = []
        total_matches = 0
        
        for log_file in all_log_files:
            matches = search_in_file(log_file, search_string)
            if matches:
                rel_path = os.path.relpath(log_file, extraction_dir)
                results[rel_path] = matches
                files_with_matches.append(log_file)
                total_matches += len(matches)
                file_type = "compressed" if is_compressed_file(log_file) else "uncompressed"
                print(f"Found {len(matches)} matches in {rel_path} ({file_type})")
        
        # Step 5: Copy matching files to output directory
        if files_with_matches:
            print(f"Copying {len(files_with_matches)} files with matches...")
            copy_matching_files(files_with_matches, extracted_dir, extraction_dir)
        
        # Step 6: Generate results summary
        result_file = os.path.join(output_dir, 'result.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"Search Results for: '{search_string}'\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Total files searched: {len(all_log_files)}\n")
            f.write(f"  - Uncompressed: {len(log_files)}\n")
            f.write(f"  - Compressed: {len(compressed_log_files)}\n")
            f.write(f"Files with matches: {len(files_with_matches)}\n")
            f.write(f"Total matches found: {total_matches}\n\n")
            
            if results:
                f.write("Detailed Results:\n")
                f.write("-" * 30 + "\n\n")
                
                for file_path, matches in results.items():
                    file_type = "compressed" if any(pattern in file_path for pattern in ['.gz', '.log.gz_']) else "uncompressed"
                    f.write(f"File: {file_path} ({file_type})\n")
                    f.write(f"Matches: {len(matches)}\n")
                    f.write("Lines:\n")
                    for line_num, line_content in matches:
                        f.write(f"  Line {line_num}: {line_content}\n")
                    f.write("\n")
            else:
                f.write("No matches found.\n")
    
    print(f"\nSearch completed!")
    print(f"Results saved to: {output_dir}/")
    print(f"Summary: {total_matches} matches found in {len(files_with_matches)} files")
    
    if files_with_matches:
        print(f"Extracted log files with matches saved to: {extracted_dir}/")

if __name__ == "__main__":
    main()
