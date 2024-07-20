#!/usr/bin/env python

# Opens files in directory, outputs firebase URLs to a file, downloads them, and replaces the links with a link to the new files.
# To use, replace PATH in the variable vaultDir with your vault's root directory.
# This automatically puts filenames in /assets - change the newFilePath variable if you want to change this

import re
import os
import requests
import calendar
import shutil
import sys
import time
from io import BytesIO

vaultDir = '/Users/nic/Desktop/test2021'
vaultDir = sys.argv[1]
print(f'vaultDir = [{vaultDir}]')
# NOTE: need to ignore .git directory!
# Maybe just look for *.md files
# sys.exit()

firebaseShort = 'none'
fullRead = 'none'
fileFullPath = ''
fullTempFilePath = ''

IMAGES_DIR_RELATIVE = 'images'  # for images and pdfs
IMAGES_DIR_FULL = f'{vaultDir}/{IMAGES_DIR_RELATIVE}'  # images, pdfs, etc
i = 0
file_number = 0
image_file_number = 0
ext = ''
if not os.path.exists(IMAGES_DIR_FULL):
    os.makedirs(IMAGES_DIR_FULL)

# Walk through all files in all directories within the specified vault directory
for dirpath, dirnames, filenames in os.walk(vaultDir):
    for filename in filenames:
        file_number += 1
        fileFullPath = os.path.join(dirpath,filename)
        print(f'file [{file_number}]: [{fileFullPath}]')
        filehandle = open(fileFullPath, errors='strict')
        for line in filehandle:
            # Download the Firebase file and save it in the images directory
            if 'firebasestorage' in line:
                try:
                    # If it's a PDF, it will be in the format {{pdf: link}}
                    if '{{pdf:' in line:
                        link = re.search(r'https://firebasestorage(.*)\?alt(.*)\}', line)
                    else:
                        link = re.search(r'https://firebasestorage(.*)\?alt(.*)\)', line)
                    firebaseShort = 'https://firebasestorage' + link.group(1) # https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FDownloadMyBrain%2FLy4Wel-rjk.png
                    firebaseUrl = link.group(0)[:-1] # https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FDownloadMyBrain%2FLy4Wel-rjk.png?alt=media&token=0fbafc8f-0a47-4720-9e68-88f70803ced6

                    # Download the file
                    print(f'requests.get({firebaseUrl})')
                    request = requests.get(firebaseUrl)

                    # Write the file to disk
                    # e.g., timestamp == 1721501543
                    timestamp = calendar.timegm(time.gmtime())
                    # Get file extension of file. Ex: .png; .jpeg
                    reg = re.search(r'(.*)\.(.+)', firebaseShort[-5:]) # a.png / .jpeg
                    ext = '.' + reg.group(2) # .jpeg
                    # Create new local file out of downloaded firebase file
                    newFilePath = f'{IMAGES_DIR_RELATIVE}/{timestamp}_{i}{ext}'
                    # print(firebaseUrl + '>>>' + newFilePath)
                    print(f'writing [{newFilePath}]')
                    with open(vaultDir + '/' + newFilePath,'wb') as output_file:
                        shutil.copyfileobj(BytesIO(request.content), output_file)
                except AttributeError: # This is to prevent the AttributeError exception when no matches are returned
                    print(f'ERROR:  AttributeError: line=[{line}] fileFullPath=[{fileFullPath}]')
                    continue
                # Save Markdown file with new local file link as a temp file
                # If there is already a temp version of a file, open that.
                fullTempFilePath = vaultDir + '/temp_' + filename
                if os.path.exists(fullTempFilePath):
                    fullRead = open(fullTempFilePath, errors='strict')
                else:
                    fullRead = open(fileFullPath, errors='strict')
                data = fullRead.read()
                data = data.replace(firebaseUrl, newFilePath)
                print(f'writing to [{fullTempFilePath}]')
                with open(fullTempFilePath,'wt') as temp_file:
                    temp_file.write(data)
                    i = i + 1
                if os.path.exists(fullTempFilePath):
                    print(f'rename file from:\n [{fullTempFilePath}] to:\n [{fileFullPath}]')
                    os.replace(src=fullTempFilePath, dst=fileFullPath)
                fullRead.close()
        filehandle.close()
