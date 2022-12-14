# Python script for modifying iso images and repackaging them

# ESXI runs a minimal install of busybox, which lacks most of the utilities found in it's linux cousins

# Linux like utilities for BusyBox
# https://github.com/brgl/busybox/tree/master/util-linux

import re
import difflib
import requests
import xml.etree.ElementTree as ET

# Import functions from other files
from unattended import xml_data
from powershell_scripts import *


# Define function for searching for a string or substring within a list
def search(string, string_list):
    # Search for the closest match using difflib
    results = difflib.get_close_matches(string, string_list)
    
    return results
    

# Define a function to mount and extract iso file
def extract_files(ssh_client, iso_file):
    # Default path for iso file storage on proxmox
    default_path = "/var/lib/vz/template/iso/"
    # Full path to current iso image
    current_path = "/var/lib/vz/template/iso/{}".format(iso_file)

    # Check to see if file exists
    stdin, stdout, stderr = ssh_client.exec_command('[ ! -f "{}" ] && echo "File not found."'.format(current_path))
    file_check = stdout.read().decode("utf-8").strip()
    if "File not found." in file_check:
        print("Error. ISO image not found.")
    else:
        print("ISO image {} found. Continuing...".format(iso_file))
        # Make directory to hold iso files
        # If directory exists, delete it and recreate it
        iso_output_path = default_path + "temp_iso_files/"
        stdin, stdout, stderr = ssh_client.exec_command('[ ! -d "{}" ] && echo "Directory not found."'.format(iso_output_path))
        directory_check = stdout.read().decode("utf-8").strip()
        if "Directory not found." in directory_check:
            # Create new directory if not found
            stdin, stdout, stderr = ssh_client.exec_command("mkdir {}".format(iso_output_path))
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print("Failed to create directory with error code: {}".format(exit_status))
        else:
            # Delete and recreate directory if found
            stdin, stdout, stderr = ssh_client.exec_command("rm -rf {}".format(iso_output_path))
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print("Failed to delete directory with error code: {}".format(exit_status))
            # Create new directory
            stdin, stdout, stderr = ssh_client.exec_command("mkdir {}".format(iso_output_path))
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print("Failed to create directory with error code: {}".format(exit_status))
        
        # Mount iso image
        stdin, stdout, stderr = ssh_client.exec_command("mount -o loop {} /mnt/".format(current_path))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print("Failed to mount iso image {} with error code: {}".format(current_path, exit_status))
        
        # Copy image contents to directory made previously
        stdin, stdout, stderr = ssh_client.exec_command("cp -r /mnt/ {}".format(iso_output_path))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print("Failed to copy files with error code: {}".format(exit_status))
        
        # Unmount iso image
        stdin, stdout, stderr = ssh_client.exec_command("umount /mnt")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print("Failed to unmount iso image with error code: {}".format(exit_status))

    # Return the final path to the files
    final_path = iso_output_path + "mnt/"

    return final_path, iso_output_path


# Define a function to modify windows images
def modify_windows(ssh_client, file_name, os, apps=["chrome", "notepad++", "7zip"]):
    # Extract the windows files
    file_path, output_path = extract_files(ssh_client, file_name)

    # Default path for iso file storage on proxmox
    default_path = "/var/lib/vz/template/iso/"
    # Remove the .iso from the filename
    iso_name = re.match("^([^.]+)", str(file_name))[0]
    # Print message
    print("Modifying iso image: {}".format(iso_name))
    
    #
    # Find a way to dynamically get the contents of the unattended file example
    #
    
    # Create directory for setup scripts
    # ADD in check to see if this path already exists
    script_directory = file_path + "sources/\$OEM\$/\$\$/Setup/Scripts/"
    stdin, stdout, stderr = ssh_client.exec_command("mkdir -p {}".format(script_directory))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to create script directory with error code: {}".format(exit_status)) 
    
    # Write scripts to their respective files
    # Get the function names of install function scripts
    application_functions = get_functions()
    script_save_names = []
    # Install the respective applications
    if len(apps) > 0:
        print("Writing default applications to ISO image...")
        # Get all code for each default application to be installed
        for app in apps:
            app_name = str(app).lower()
            app_name = ''.join(letter for letter in app_name if letter.isalnum())
            matches = [match for match in application_functions if app_name in match]
            # Lookup function name and call it
            if len(matches) > 0:
                method = eval(str(matches[0]))
                code, save_name = method()
                script_save_names.append(save_name)
                # Write code to the respective powershell files
                stdin, stdout, stderr = ssh_client.exec_command("echo '{}' >> {}{}".format(code, script_directory, save_name))
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    print("Failed to write {} script to file with error code: {}".format(app_name, exit_status))
                    
    # Write virtio driver install script to iso file
    driver_code, driver_save_name = install_virtio()
    stdin, stdout, stderr = ssh_client.exec_command("echo '{}' >> {}{}".format(driver_code, script_directory, driver_save_name))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to write virtio driver install script to file with error code: {}".format(exit_status))
    # Add run command to unattend xml file
    script_save_names.append(driver_save_name)
                    
    # Write windows update script to iso file
    update_code, update_save_name = install_updates()
    stdin, stdout, stderr = ssh_client.exec_command("echo '{}' >> {}{}".format(update_code, script_directory, update_save_name))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to write windows update script to file with error code: {}".format(exit_status))
    # Add run command to unattend xml file
    script_save_names.append(update_save_name)
        
    
    # Defaults for iso image hostname and password
    default_hostname = "temp-host"
    default_password = "temp_password"
    
    # Print default message
    print("\n  Setting defaults for iso image: ")
    print("  - Hostname: {}".format(default_hostname))
    print("  - Administrator password: {}\n".format(default_password))
    
    # Get xml data
    if "2022" in str(os):
        # Set version to Server 2022 Standard
        xml = xml_data(default_hostname, default_password, "Windows Server 2022 SERVERSTANDARD", script_save_names)
    elif "2019" in str(os):
        # Set version to Server 2019 Standard
        xml = xml_data(default_hostname, default_password, "Windows Server 2019 SERVERSTANDARD", script_save_names)
    elif "2016" in str(os):
        # Set version to Server 2016 Standard
        xml = xml_data(default_hostname, default_password, "Windows Server 2016 SERVERSTANDARD", script_save_names)
    elif "2012" in str(os):
        # Set version to Server 2012 Standard
        xml = xml_data(default_hostname, default_password, "Windows Server 2012 SERVERSTANDARD", script_save_names)
    else:
        # Default to Server 2019 Standard if version can't be parsed
        print("Unknown Server variant. Defaulting to Server 2019.")
        xml = xml_data(default_hostname, default_password, "Windows Server 2019 SERVERSTANDARD", script_save_names)
    
    #xml_data = xml_data_2019(default_hostname, default_password, script_save_names)
    # Escape broken characters
    xml = xml.replace('\r', "\\r")
    xml = xml.replace('\v', "\\v")
    
    # Write xml data to file
    stdin, stdout, stderr = ssh_client.exec_command("echo '{}' >> {}Autounattend.xml".format(str(xml), file_path))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to create unattend.xml file with error code: {}".format(exit_status))

    # Repackage the windows iso file
    stdin, stdout, stderr = ssh_client.exec_command("mkisofs -allow-limited-size -b boot/etfsboot.com -no-emul-boot -J -l -R -V '{}' -iso-level 4 -o {}_auto.iso {}".format(iso_name, str(default_path + iso_name), file_path))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to create new iso image with error code: {}".format(exit_status))
        
    # Cleanup
    stdin, stdout, stderr = ssh_client.exec_command("rm -rf {}".format(output_path))
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to cleanup: {}".format(exit_status))
    
    # Return Final iso save name
    iso_save_name = str(iso_name) + "_auto.iso"

    return iso_save_name

