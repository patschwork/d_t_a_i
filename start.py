#!/usr/bin/python
# -*- coding: utf-8 -*-

## $Date: 2015/10/03 19:22:59 $
## $Revision: eeb943e510ac $

import os
import hashlib
import time
import fnmatch
import shutil
import json
import sys

debug=0

# Default parameter
param_check_intervall = 2	# seconds
param_fileversion_sep = "_v"
param_init_number = "0001"
param_start_init_fileversion = param_fileversion_sep+param_init_number
param_method_change_detect = "content"

# get current path of my script
script_dir = os.path.dirname(os.path.abspath(__file__))

key_file_not_exists = "File doesn't exists!"

filelist_path = ""

# Command Line Parameters will be detected here
def cli_params():
    if (debug==1):
        print len(sys.argv)
    global filelist_path
    if len(sys.argv) != 2:
        print "You must call me like:"
        print "   start.py <path/file_to_observe.json>"
        raise Exception("Call parameter missing!")
        sys.exit(1)
	filelist_path = sys.argv[1]
	
# Load the list, where to find the files to be observed
def load_filelist(filelist_path):
	global files_to_observe
	filelist_file = os.path.join(filelist_path, 'file_to_observe.json')
	json_data = open(filelist_file)
	files_to_observe = json.load(json_data)
	
# Load the config of the application und set the parameters
def load_config(config_path):
    global config
    config_file = os.path.join(config_path, 'config.json')
	# read the config
    json_data = open(config_file)
    config = json.load(json_data)
	
    param_check_intervall = config["params"]["check_intervall"]
    param_fileversion_sep = config["params"]["fileversion_sep"]
    param_init_number = config["params"]["init_number"]
    param_method_change_detect = config["params"]["method_change_detect"]

# Print only, if debug is on
def dprint(text):
    if (debug==1):
        print text

# Create a hash out of the content of a file. This is used in function get_needed_file_attr
def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

# Create a MD5 Hash 
def get_needed_file_attr(filename, when):
    if (os.path.isfile(filename)):
        attr = os.stat(filename)
		# build a key of the content
        if (param_method_change_detect=="content"):
            dprint(">> Use content change detection")
            retValue = hashfile(open(filename, 'rb'), hashlib.sha256())
        # build a key with file metrics
        else:
            dprint(">> Use filenamesize and -time change detection")
            retValue = hashlib.md5(str(attr.st_size) + str(attr.st_mtime)).hexdigest()
    else:
        retValue = key_file_not_exists
        #if (when=="during observation"):
			#print "File doesn't exists anymore!!! Was it renamed, moved or deleted?"
    return retValue

# Compare file hash
def check_against_old_hash(id_to_check, current_hash):
	retValue = False	# keine Aenderung
	this_id=""
	if (files_attr.get(id_to_check)!=current_hash):
		retValue = True
	return retValue

# Get max. file version number
def get_highest_version_number(id_for_highest_number):
    retValue = ""
    
    fobj = files_to_observe.get(id_for_highest_number)
    filenameToCheck = ""
    init_filename = "<not set>"
    dprint(">> (get_highest_version_number), fobj.get(key_Save_To_Same_Folder): " + fobj.get(key_Save_To_Same_Folder))
    if (fobj.get(key_Save_To_Same_Folder)=="True"):
        filenameToCheck = fobj.get(key_Filename)
        f_path = os.path.dirname(filenameToCheck)
        f_only = os.path.basename(os.path.splitext(filenameToCheck)[0])
        f_ext = extension = os.path.splitext(filenameToCheck)[1]
        init_filename = os.path.join(f_path,f_only+param_start_init_fileversion+f_ext)
    else:
        alternateFolderToSave = fobj.get(key_Alternate_Backup_Folder)
        dprint(">> (get_highest_version_number), alternateFolderToSave: " + alternateFolderToSave)
        filenameToCheck = fobj.get(key_Filename)
        f_path = os.path.dirname(alternateFolderToSave)
        if (os.path.isdir(f_path)==False):
           # Als Fallback, wenn Backupverzeichnis nicht existiert, dann im eigenen Verzeichnis sichern
           dprint(">> (get_highest_version_number), os.path.isdir(f_path): " + "False")
           f_path = os.path.dirname(filenameToCheck)
        f_only = os.path.basename(os.path.splitext(filenameToCheck)[0])
        f_ext = extension = os.path.splitext(filenameToCheck)[1]
        init_filename = os.path.join(f_path,f_only+param_start_init_fileversion+f_ext)
        #raise Exception("Not implemented, yet")
    # Check, if there is a number one ;-)
    if (os.path.isfile(init_filename)):
        # create next number
        lastfile = ""
        for pathentry in os.walk(f_path, False):    
            for file in sorted(pathentry[2]):    # sorted, damit auch ordentlich nach oben gezaehlt wird
                if fnmatch.fnmatch(file, f_only+param_fileversion_sep+'*'+f_ext):
                    lastfile = file    # vertrauen wir darauf, dass das die hoechste Version ist!
        f_only_last = os.path.basename(os.path.splitext(lastfile)[0])
        #split up, to get the number
        current_number_str = f_only_last.split(param_fileversion_sep)[1]
        current_number_int = int(current_number_str)
        new_number = current_number_int + 1
        # format into leading 0 as a string
        new_formatted_number = format_new_number(new_number)
        # build the new filename
        new_filename = os.path.join(f_path,f_only+param_fileversion_sep+new_formatted_number+f_ext)
        retValue = new_filename
    else:
        # use the v0001
        retValue = init_filename
    if (init_filename == "<not set>"):
        raise Exception("init_filename could not be set!")
    
    return retValue

# Convert number to alphanumeric string
def format_new_number(new_number):
	retValue = ""
	for i in range(0, len(param_init_number)-len(str(new_number))):
		retValue = retValue + '0'
	return retValue+str(new_number)

# make a copy if md5 hash has changed
def create_copy_new_fileversion(id_for_the_fileversion, newversionfilename):
    fobj = files_to_observe.get(id_for_the_fileversion)
    fname = fobj.get(key_Filename)
    shutil.copy(fname, newversionfilename)

# only for testing
# which_file = raw_input('Give me the name of the file to be watched? ')

# Load constants and config params
key_Save_To_Same_Folder = "key_Save_To_Same_Folder"
key_Filename = "key_Filename"
key_Alternate_Backup_Folder = "key_Alternate_Backup_Folder"

cli_params()
load_config(script_dir)
load_filelist(filelist_path)

files_attr = {}

# # init - set beginning values
for (id, fobj) in files_to_observe.items():
    fname = fobj.get(key_Filename)
    if (debug==1):
        print id, fobj, get_needed_file_attr(fname,"init")
	files_attr.update({id: get_needed_file_attr(fname,"init")})
    
while 1==1:
        time.sleep(param_check_intervall)
        id=0
        for (id, fobj) in files_to_observe.items():
            fname = fobj.get(key_Filename)
            check = get_needed_file_attr(fname,"during observation")
            if (check!=key_file_not_exists):
                dprint(">>fname, check: " + fname + ", " + unicode(check))
                newversion = check_against_old_hash(id, check)
                if (newversion):
                    newfileversionname = get_highest_version_number(id)
                    dprint("change detected, creating a new file: " + newfileversionname)
                    create_copy_new_fileversion(id,newfileversionname)
                    files_attr.update({id: check})
