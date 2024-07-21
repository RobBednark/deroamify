#!/usr/bin/env python

# ./downloadfirebase.py [directory]
# e.g.,
#   python downloadfirebase.py .
# Opens files in directory, outputs firebase URLs to a file, downloads them, and replaces the links with a link to the new files.
# The downloaded files are saved in ".../images"

import calendar
import hashlib
from io import BytesIO
import os
import re
import shutil
import sys
import time
import traceback

import requests

inputDir = sys.argv[1]
print(f'inputDir = [{inputDir}]')

fullRead = 'none'
fileFullPath = ''
fullTempFilePath = ''

IMAGES_DIR_RELATIVE = 'images'  # for images and pdfs
IMAGES_DIR_FULL = f'{inputDir}/{IMAGES_DIR_RELATIVE}'  # images, pdfs, etc
file_number_markdown = 0
image_file_number = 1
url2filename = {}  # key: url; value: hexdigest.ext;  e.g., url2checksum['https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf'] = '0cc175b9c0f1b6a831c399e269772661.pdf'
firebase2local = {}  # key: firebase url; value: local path;   e.g., firebase2local['https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf'] = 'images/0cc175b9c0f1b6a831c399e269772661.pdf'
if not os.path.exists(IMAGES_DIR_FULL):
    os.makedirs(IMAGES_DIR_FULL)

# Walk through all files in all directories in inputDir
for dirpath, dirnames, filenames in os.walk(inputDir):
    # ignore the IMAGES_DIR_RELATIVE directory
    if dirpath == IMAGES_DIR_FULL:
        print(f'skipping: dirpath=[{dirpath}]')
        continue
    if dirpath.startswith('./.obsidian'):
        print(f'skipping: dirpath=[{dirpath}]')
        continue

    for filename in filenames:
        file_number_markdown += 1
        fileFullPath = os.path.join(dirpath,filename)
        print(f'markdown file [{file_number_markdown}]: [{fileFullPath}]')
        fh_input = open(fileFullPath, mode='r+', errors='strict')
        firebase_urls_found = []
        for line in fh_input:
            # Download the Firebase file and save it in the images directory
            #if 'https://firebasestorage' in line:
            if 'firebasestorage' in line:
                match = re.search(r'https://firebasestorage(.*)\?alt(.*?)[\)\}]', line)  # ".*?" is non-greedy -- stop at the first ) or }.
                if not match:
                    print(f'ERROR: no match found for line=[{line}] \n   fileFullPath=[{fileFullPath}]')
                # e.g., input line:
                #   - {{[[pdf]]: https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf?alt=media&token=89430094-7f61-4cbf-8799-b298359f3469}}
                #                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                #                                       group(1)                                                                                                    group(2)
                #                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                #                group(0) (entire match, including the final '))' or '}}')

                # e.g., match.group(0) (entire match):
                #   https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf?alt=media&token=89430094-7f61-4cbf-8799-b298359f3469}}
                firebaseUrl = match.group(0)[:-1]  # group(0) is the entire match; strip the final character, a ')' or '}'

                # e.g., match.group(1):
                #   .googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf
                # e.g., firebaseShort:
                #   https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf
                firebaseShort = 'https://firebasestorage' + match.group(1)

                # Get file extension, eg., .png .jpeg .pdf
                match = re.search(r'.*(\..+)', firebaseShort[-5:])
                file_extension = match.group(1)

                md5_filename = hashlib.md5(firebaseUrl.encode('utf-8')).hexdigest()
                md5_filename += file_extension
                if url2filename.get(firebaseUrl) and (url2filename.get(firebaseUrl) != md5_filename):
                    print(f'ERROR:  firebaseUrl=[{firebaseUrl}] existing digest = [{url2filename[filebaseUrl]}]  new digest = [{md5_filename}]')
                    sys.exit(1)

                newFilePath = f'{IMAGES_DIR_RELATIVE}/{md5_filename}'  # e.g., images/0cc175b9c0f1b6a831c399e269772661.pdf
                output_path = f'{inputDir}/{newFilePath}'
                firebase2local[firebaseUrl] = newFilePath
                firebase_urls_found.append(firebaseUrl)
                if os.path.exists(output_path):
                    print(f'NOTE: already downloaded: [{firebaseUrl}]  [{output_path}]')
                else:
                    url2filename[firebaseUrl] = md5_filename
                    # Download the file
                    print(f'requests.get({firebaseUrl})')
                    request = requests.get(firebaseUrl)
                    print(f'writing [{output_path}]')
                    with open(output_path, 'wb') as fh_output:
                        shutil.copyfileobj(BytesIO(request.content), fh_output)
        # Replace each of the urls found
        if firebase_urls_found:
            fh_input.seek(0)  # rewind to the beginning of the file
            file_contents = fh_input.read()
            fh_input.seek(0)
            fh_input.truncate() 
            for firebase_url in firebase_urls_found:
                # Replace the firebase url with the local file path
                local_path = firebase2local[firebase_url]
                file_contents = file_contents.replace(firebase_url, local_path)
            fh_input.write(file_contents)
        fh_input.close()
