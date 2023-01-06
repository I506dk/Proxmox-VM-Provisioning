import yaml
import json


# Define a function to print out a dictionary
def print_dictionary(dictionary, depth=1):
    for key in dictionary:
        print("{} - {}:".format((depth*'  '), key), end =" ")
        if type(dictionary[key]) == dict:
            # Nested dictionary
            new_depth = depth + 1
            print_dictionary(dictionary[key], new_depth)
        else:
            if type(dictionary[key]) != list:
                if (str(key) == "disk") or (str(key) == "memory"):
                    print(" {} (GB)".format(dictionary[key]))
                else:
                    print(" {}".format(dictionary[key]))
            else:
                print()
                for item in dictionary[key]:
                    print("  {}{}".format((depth*2*'  '), item))                
    print()
                
    return


# Define function to load yaml file configurations and parse them.
def load_configs(yaml_file="virtual_machines.yaml"):
    with open(yaml_file, "r") as yamlfile:
        try:
            data = yaml.safe_load(yamlfile)
            print("\nConfiguration file data imported successfully.")
        except yaml.YAMLError as exc:
            print("\nError loading file: {}".format(exc))

    # Return a dictionary of data read in from the yaml config file
    return data
        
        
# Define function to parse the yaml data
def parse_yaml(yaml_data):
    # There should be two main keys in the yaml data
    # Resources, which define virtual machines and their specific configurations,
    # And defaults, which define defaults to be applied to all VMs

    # Parse VM resources
    if yaml_data.__contains__("resources"):
        # Initialize a list of VM configs
        vm_configuations = []
        #vm_configuations = {}
        for config in yaml_data["resources"]:
            if config.__contains__("virtual machine"):
                vm_configuations.append(config["virtual machine"])
                #vm_configuations["virtual machine"] = config["virtual machine"]
            else:
                print("\nUnknown configuration found under resources:\n {}".format(config))
    
    # Parse VM defaults
    if yaml_data.__contains__("defaults"):
        # Initialize a dictionary of defaults to be applied
        defaults = {}
        for config in yaml_data["defaults"]:
            if config.__contains__("applications"):
                defaults["applications"] = config["applications"]
            else:
                print("Unknown configuration found under defaults:\n {}".format(config))
                defaults["applications"] = []

    # Print configuration data
    print("\nDefaults to be applied to all virtual machines:")
    print_dictionary(defaults)
    print("Virtual machine configurations:")
    for configuration in vm_configuations:
        print("  Current virtual machine configuration:")
        print_dictionary(configuration, 1)

    return vm_configuations, defaults

