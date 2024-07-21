#!/usr/bin/env python

# ./downloadfirebase.py [directory]
# e.g.,
#   python downloadfirebase.py .
# Opens files in directory, outputs firebase URLs to a file, downloads them, and replaces the links with a link to the new files.
# Files are This automatically puts filenames in /assets - change the newFilePath variable if you want to change this

import re
import os
import requests
import calendar
import shutil
import sys
import time
import traceback
from io import BytesIO

inputDir = '/Users/nic/Desktop/test2021'
inputDir = sys.argv[1]
print(f'inputDir = [{inputDir}]')
# NOTE: need to ignore .git directory!
# Maybe just look for *.md files
# sys.exit()

firebaseShort = 'none'
fullRead = 'none'
fileFullPath = ''
fullTempFilePath = ''

IMAGES_DIR_RELATIVE = 'images'  # for images and pdfs
IMAGES_DIR_FULL = f'{inputDir}/{IMAGES_DIR_RELATIVE}'  # images, pdfs, etc
file_number = 0
image_file_number = 1
ext = ''
if not os.path.exists(IMAGES_DIR_FULL):
    os.makedirs(IMAGES_DIR_FULL)

# Walk through all files in all directories within the specified vault directory
for dirpath, dirnames, filenames in os.walk(inputDir):
    # ignore the IMAGES_DIR_RELATIVE directory
    if dirpath == IMAGES_DIR_FULL:
        print(f'skipping: dirpath=[{dirpath}]')
        continue

    for filename in filenames:
        file_number += 1
        fileFullPath = os.path.join(dirpath,filename)
        print(f'file [{file_number}]: [{fileFullPath}]')
        filehandle = open(fileFullPath, errors='strict')
        for line in filehandle:
            # Download the Firebase file and save it in the images directory
            #if 'https://firebasestorage' in line:
            if 'firebasestorage' in line:
                try:
                    # If it's a PDF, it will be in the format {{pdf: link}}
                    if '{{pdf:' in line:
                        match = re.search(r'https://firebasestorage(.*)\?alt(.*)\}', line)
                    else:
                        match = re.search(r'https://firebasestorage(.*)\?alt(.*)\)', line)
                    # e.g., input line:
                    #   - {{[[pdf]]: https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf?alt=media&token=89430094-7f61-4cbf-8799-b298359f3469}}
                    #                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                    #                                       group(1)                                                                                                    group(2)

                    # e.g., match.group(0):
                    #   .googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf
                    # e.g., firebaseUrl:
                    #   .googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Frob_graph_1_2021-03-05%2FFUVL4EDjUx.pdf (strip final character, presumably the newline)
                    firebaseUrl = match.group(0)[:-1]

                    # e.g., match.group(1):
                    #   =media&token=89430094-7f61-4cbf-8799-b298359f3469}}
                    # e.g., firebaseShort:
                    #   https://firebasestorage=media&token=89430094-7f61-4cbf-8799-b298359f3469}}
                    
                    firebaseShort = 'https://firebasestorage' + match.group(1)

                    # Download the file
                    print(f'requests.get({firebaseUrl})')
                    request = requests.get(firebaseUrl)

                    # Write the file to disk
                    # e.g., timestamp == 1721501543
                    timestamp = calendar.timegm(time.gmtime())
                    # Get file extension of file. Ex: .png; .jpeg
                    match = re.search(r'(.*)\.(.+)', firebaseShort[-5:]) # a.png / .jpeg
                    ext = '.' + match.group(2) # .jpeg
                    # Create new local file out of downloaded firebase file
                    newFilePath = f'{IMAGES_DIR_RELATIVE}/{timestamp}_{image_file_number}{ext}'
                    # print(firebaseUrl + '>>>' + newFilePath)
                    print(f'writing [{newFilePath}]')
                    with open(inputDir + '/' + newFilePath,'wb') as output_file:
                        shutil.copyfileobj(BytesIO(request.content), output_file)
                except AttributeError: # This is to prevent the AttributeError exception when no matches are returned
                    print(f'ERROR:  AttributeError: line=[{line}] fileFullPath=[{fileFullPath}]')
                    # Print all the details of the exception
                    print(traceback.format_exc())
                    # sys.exit(1)
                    continue
                # Save Markdown file with new local file link as a temp file
                # If there is already a temp version of a file, open that.
                fullTempFilePath = inputDir + '/temp_' + filename
                if os.path.exists(fullTempFilePath):
                    fullRead = open(fullTempFilePath, errors='strict')
                else:
                    fullRead = open(fileFullPath, errors='strict')
                data = fullRead.read()
                data = data.replace(firebaseUrl, newFilePath)
                print(f'writing to [{fullTempFilePath}]')
                with open(fullTempFilePath,'wt') as temp_file:
                    temp_file.write(data)
                    image_file_number += 1
                if os.path.exists(fullTempFilePath):
                    print(f'rename file from:\n [{fullTempFilePath}] to:\n [{fileFullPath}]')
                    os.replace(src=fullTempFilePath, dst=fileFullPath)
                fullRead.close()
        filehandle.close()
