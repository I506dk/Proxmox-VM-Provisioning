# Python script to provision virtual machines on Proxmox host

import re
import time
import yaml
import difflib
import paramiko

# Import functions from other files
from modify_iso import extract_files
from modify_iso import modify_windows
from load_configs import load_configs
from load_configs import parse_yaml

# Credentials for logging in via ssh
username = "root"
password = "<password>"

# Proxmox host ip address
host = "<ip_address>"


# Define function to get the key for a specific value
def get_key(val, dictionary):
    for key, value in dictionary.items():
        if val == value:
            return key
        
    return "Key does not exist."


# Define function for searching for a string or substring within a list
def search(string, string_list):
    # Search for the closest match using difflib
    results = difflib.get_close_matches(string, string_list)
    
    return results


# Define function to get data from the esxi host
def get_host_data(ssh_client):
    # Get proxmox host specs
    # Get total system memory
    stdin, stdout, stderr = ssh_client.exec_command("grep MemTotal /proc/meminfo")
    physical_memory = stdout.read().decode("utf-8").strip()
    physical_memory = round(int(re.findall(r'\b\d+\b', physical_memory)[0])/1000)
    
    # Get total number of physical cpus
    stdin, stdout, stderr = ssh_client.exec_command("nproc --all")
    physical_cores = stdout.read().decode("utf-8").strip()
    
    # Get free disk space or total or used or something
    # lsblk
    
    
    
    # Get all iso files found on disk
    # By default the script will look for iso files on the proxmox host
    stdin, stdout, stderr = ssh_client.exec_command("find /var/lib/vz/template/iso -maxdepth 1 -type f")
    iso_files = stdout.read().decode("utf-8").strip().split('\n')
    for file in iso_files:
        # Get only the file name, not the full path
        iso_file_name = re.findall(r'([^\/]+$)', file)[0]
        # Replace the list item with just the iso file name
        iso_files = list(map(lambda x: x.replace(file, iso_file_name), iso_files))
    
    # Print message
    print("ISO files available for use: \n{}\n".format(iso_files))
    
    # Get existing virtual machines
    stdin, stdout, stderr = ssh_client.exec_command("qm list")
    # Parse output into dictionary
    output = stdout.read().decode("utf-8").strip().split('\n')
    vm_list = []
    for vm in output:
        current_vm = vm.strip().split(' ')
        current_vm = [i for i in current_vm if i]
        vm_list.append(current_vm)

    header = vm_list[0]
    existing_vms = [dict(zip(header, vm)) for vm in vm_list[1:]]
    
    # Print message
    print("Existing virtual machines found on host: {}".format(len(existing_vms)))

    return physical_memory, physical_cores, existing_vms, iso_files


# Define a function to calculate limits for virtual machines
def calculate_limits(total_memory, existing_configs):
    # Memory limits will be based off of raw physical memory
    memory_in_use = 0 # (MB)
    disk_in_use = 0 # (GB)
    starting_id = 100
    
    if len(existing_configs) > 0:
        # Calculate the current memory allocated to virtual machines
        for config in existing_configs:
            if config.__contains__("MEM(MB)"):
                memory_in_use += int(config["MEM(MB)"])
        # Print memory message
        print("\nTotal memory allocated to virtual machines: {} out of {} (MB)".format(str(memory_in_use), str(total_memory)))
        
        # Calculate the current disk space allocated to virtual machines
        for config in existing_configs:
            if config.__contains__("BOOTDISK(GB)"):
                disk_in_use += int(float(config["BOOTDISK(GB)"]))
        # Print disk message
        print("\nTotal disk space allocated to virtual machines: {} out of {} (GB)".format(str(disk_in_use), str(200)))
        
        # Initialize a list of VM IDs
        id_list = []
        # Get all existing VM IDs
        for config in existing_configs:
            if config.__contains__("VMID"):
                id_list.append(int(config["VMID"]))
        # Setting the starting id to be right after the highest existing id
        starting_id = max(id_list) + 1
        
    else:
        print("\nNo existing virtual machines found. Continuing...")
        
    # Calculate the amount of free memory that can be allocated to VMs
    free_memory = int(total_memory) - int(memory_in_use)

    return free_memory, starting_id
    

# Define a function to create a virtual machine
def create_vm(ssh_client, vm_number, full_iso, vm_name, memory, cores, disk, sockets=1):
    # Command to create a virtual machine along with the respective disk
    # Set vm to autostart --start 1
    create_command = 'qm create {} --ide2 {},media=cdrom --name {} --memory {} --sockets {} --cores {} --net0 e1000,bridge=vmbr0,firewall=1 --boot order="ide0;ide2;net0" --scsihw virtio-scsi-single --ide0 local-lvm:{} --agent enabled=1 --start 1'.format(
        vm_number,
        full_iso,
        vm_name,
        memory,
        sockets,
        cores,
        disk
    )
    
    # Create the virtual machine
    stdin, stdout, stderr = ssh_client.exec_command(create_command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print("Failed to create virtual machine with error code: {}".format(exit_status))

    return
    

# Define function to validate all virtual machine configurations
def validate():
    return

    
# Function to login to ssh service for a given ip or hostname
def ssh_connect(hostname, username, password, port=22):
    # setup ssh client, and set key policies (for unknown hosts mainly)
    client = paramiko.SSHClient()
    # Load SSH host keys on current machine
    client.load_system_host_keys()
    # Reject unknown host keys (If unknown, there is potential for compromise)
    #client.set_missing_host_key_policy(paramiko.RejectPolicy())
######### Figure out way to load current machine host keys ####################################
    # AutoAdd will allow SSH session with unknown machine (For first time connecting)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Set default timeout
    banner_timeout = 10
    
    # Establish connection, run commands, and return command(s) output
    try:
        # Connect to client machine
        client.connect(hostname, port, username, password, banner_timeout=banner_timeout)
        ssh_session = client.get_transport()
        
        # Get host data (iso files, VMs, specs, etc.)
        node_memory, node_cores, existing_virtual_machines, existing_iso_files = get_host_data(client)
        
        # Caluculate memory, cpu, and disk limits
        usable_memory, initial_vm_id = calculate_limits(node_memory, existing_virtual_machines)
        
        # Load VM configurations from yaml file
        # Specify path if not in current working directory
        vm_configs = load_configs()

        # Parse yaml configuration data
        current_vm_configs, vm_defaults = parse_yaml(vm_configs)

        # By default, if no ISO file is specified in the yaml config file,
        # The script will look for the corresponding OS iso and modify it.
        # Initialize list to hold operating systems to be modified
        iso_files_to_modify = []
        for virtual_machine in current_vm_configs:
            # Get all operating systems for configs that don't explicitly supply an iso path
            if not virtual_machine.__contains__("iso image path"):
                current_os = virtual_machine["operating system"]
                if str(current_os) not in iso_files_to_modify:
                    iso_files_to_modify.append(current_os)

        # Initialize list to hold modified iso image names
        # Initialize dictionary to hold modified iso image names for the respective OS
        modified_iso_images = {}
        # Modify each iso image
        for operating_system in iso_files_to_modify:
            if "windows" in str(operating_system).lower():
                # Search for the respective iso image
                iso_image = str(search(operating_system, existing_iso_files)[0])
                # Modify the windows image
                iso_image = modify_windows(client, iso_image, operating_system, vm_defaults["applications"])
                modified_iso_images[str(operating_system)] = iso_image
            else:
                print("Not a windows image")
 
        # Create each virtual machine
        for virtual_machine in current_vm_configs:
            # Get all virtual machine attributes
            if not virtual_machine.__contains__("iso image path"):
                current_iso = modified_iso_images[virtual_machine["operating system"]]
                ide0 = "local:iso/" + current_iso
                current_hostname = virtual_machine["hostname"]
                current_cores = virtual_machine["cpu"]
                current_memory = int(virtual_machine["memory"]) * 1024
                current_disk = int(virtual_machine["disk"]) * 1024
            # Use raw path if given
            else:
                ide0 = virtual_machine["iso image path"]
                current_hostname = virtual_machine["hostname"]
                current_cores = virtual_machine["cpu"]
                current_memory = int(virtual_machine["memory"]) * 1024
                current_disk = int(virtual_machine["disk"])

            # Create the virtual machine
            create_vm(client, initial_vm_id, ide0, current_hostname, str(current_memory), str(current_cores), str(current_disk))
            
            # Let the VM finish, then come back and configure each one
            
            
            # Increment the VM ID for the next VM
            initial_vm_id += 1     

    # Catch errors for failed login or connection rejection
    except paramiko.ssh_exception.AuthenticationException as error:
        print("Authentication Error. Incorrect login credentials.")
    except paramiko.ssh_exception.SSHException as error_1:
        print("Too many requests, or not enough resources. Implementing rate limiting.")
        banner_timeout += 2
    except TimeoutError as error_2:
        print("Connection attempt timed out.")
    
    # Close client when done
    client.close()
    
    return
    

 
# Beginning of main
if __name__ == '__main__':
    # Test ssh connection to proxmox
    # If successful, create virtual machines
    ssh_connect(host, username, password)

    # Print ending message
    print("Finished.")


