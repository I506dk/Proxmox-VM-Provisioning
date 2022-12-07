# Example unattended xml file for automated windows server installs
# This creates standard/default partitions and uses the whole disk allocated to the VM

# Variables that need to be dynamically changed in the xml
#username = "Administrator"
#password = "Windows_User"
#hostname = "test-server"
#operating_system = "Windows Server 2019 SERVERSTANDARD"
#timezone = "Pacific Standard Time"

# Define a function to dynamically add in powershell scripts to be run on first logon
# Order number default needs to match the last number of the non dynamic command calls in the xml_data_2019
order_number = 11
def add_powershell(script_name):
    # Script name
    regular_name = script_name.replace(".ps1", '')
    global order_number 
    order_number += 1

    command = f"""
    \t\t    <SynchronousCommand wcm:action="add">
    \t\t\t<CommandLine>cmd.exe /c C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -File C:\Windows\Setup\Scripts\{script_name}</CommandLine>
    \t\t\t<Description>Run {script_name} Script</Description>
    \t\t\t<Order>{order_number}</Order>
    \t\t    </SynchronousCommand>
    """

    return command


# Define function to create unattend.xml file
def xml_data_2019(hostname, admin_password, script_list=["install_chrome.ps1", "install_notepad.ps1", "install_7zip.ps1"], operating_system="Windows Server 2019 SERVERSTANDARD", timezone="Pacific Standard Time"):
    # Create string to add to xml data
    other_commands = ""
    
    # Add xml for each command to the above string
    for script in script_list:
        xml = add_powershell(script)
        other_commands += xml
        
    xml_data = f"""<?xml version="1.0" encoding="utf-8"?>
    <unattend xmlns="urn:schemas-microsoft-com:unattend">
        <settings pass="windowsPE">
            <component name="Microsoft-Windows-PnpCustomizationsWinPE"
                publicKeyToken="31bf3856ad364e35" language="neutral"
                versionScope="nonSxS" processorArchitecture="amd64"
                xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">            
            </component>

            <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <SetupUILanguage>
                    <UILanguage>en-US</UILanguage>
                </SetupUILanguage>
                <InputLocale>en-US</InputLocale>
                <SystemLocale>en-US</SystemLocale>
                <UILanguage>en-US</UILanguage>
                <UILanguageFallback>en-US</UILanguageFallback>
                <UserLocale>en-US</UserLocale>
            </component>
            
            <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <DiskConfiguration>
                    <Disk wcm:action="add">
                        <CreatePartitions>
                            <CreatePartition wcm:action="add">
                                <Type>Primary</Type>
                                <Order>1</Order>
                                <Size>350</Size>
                            </CreatePartition>
                            <CreatePartition wcm:action="add">
                                <Order>2</Order>
                                <Type>Primary</Type>
                                <Extend>true</Extend>
                            </CreatePartition>
                        </CreatePartitions>
                        <ModifyPartitions>
                            <ModifyPartition wcm:action="add">
                                <Active>true</Active>
                                <Format>NTFS</Format>
                                <Label>boot</Label>
                                <Order>1</Order>
                                <PartitionID>1</PartitionID>
                            </ModifyPartition>
                            <ModifyPartition wcm:action="add">
                                <Format>NTFS</Format>
                                <Label>Windows</Label>
                                <Letter>C</Letter>
                                <Order>2</Order>
                                <PartitionID>2</PartitionID>
                            </ModifyPartition>
                        </ModifyPartitions>
                        <DiskID>0</DiskID>
                        <WillWipeDisk>true</WillWipeDisk>
                    </Disk>
                </DiskConfiguration>
                <ImageInstall>
                    <OSImage>
                        <InstallFrom>
                            <MetaData wcm:action="add">
                                <Key>/IMAGE/NAME</Key>
                                <Value>{operating_system}</Value>
                            </MetaData>
                        </InstallFrom>
                        <InstallTo>
                            <DiskID>0</DiskID>
                            <PartitionID>2</PartitionID>
                        </InstallTo>
                    </OSImage>
                </ImageInstall>
                <UserData>
                    <!-- Product Key from https://www.microsoft.com/de-de/evalcenter/evaluate-windows-server-technical-preview?i=1 -->
                    <ProductKey>
                        <!-- Do not uncomment the Key element if you are using trial ISOs -->
                        <!-- You must uncomment the Key element (and optionally insert your own key) if you are using retail or volume license ISOs -->
                        <!-- <Key>6XBNX-4JQGW-QX6QG-74P76-72V67</Key> -->
                        <WillShowUI>OnError</WillShowUI>
                    </ProductKey>
                    <AcceptEula>true</AcceptEula>
                    <FullName>Administrator</FullName>
                </UserData>
            </component>
        </settings>
        <settings pass="specialize">
            <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <OEMInformation>
                    <HelpCustomized>false</HelpCustomized>
                </OEMInformation>
                <ComputerName>{hostname}</ComputerName>
                <TimeZone>{timezone}</TimeZone>
                <RegisteredOwner/>
            </component>
            <component name="Microsoft-Windows-ServerManager-SvrMgrNc" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <DoNotOpenServerManagerAtLogon>true</DoNotOpenServerManagerAtLogon>
            </component>
            <component name="Microsoft-Windows-IE-ESC" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <IEHardenAdmin>false</IEHardenAdmin>
                <IEHardenUser>true</IEHardenUser>
            </component>
            <component name="Microsoft-Windows-OutOfBoxExperience" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <DoNotOpenInitialConfigurationTasksAtLogon>true</DoNotOpenInitialConfigurationTasksAtLogon>
            </component>
            <component name="Microsoft-Windows-Security-SPP-UX" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <SkipAutoActivation>true</SkipAutoActivation>
            </component>
            <component name="Microsoft-Windows-Deployment" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <RunSynchronous>
                    <RunSynchronousCommand wcm:action="add">
                        <Order>1</Order>
                        <Description>Set Execution Policy 64 Bit</Description>
                        <Path>cmd.exe /c powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force"</Path>
                    </RunSynchronousCommand>
                    <RunSynchronousCommand wcm:action="add">
                        <Order>2</Order>
                        <Description>Set Execution Policy 32 Bit</Description>
                        <Path>cmd.exe /c powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force"</Path>
                    </RunSynchronousCommand>  
                </RunSynchronous>
            </component>
        </settings>
        <settings pass="oobeSystem">
            <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            
                <AutoLogon>
                    <Password>
                        <Value>{admin_password}</Value>
                        <PlainText>true</PlainText>
                    </Password>
                    <Enabled>true</Enabled>
                    <Username>Administrator</Username>
                </AutoLogon>
                
                <FirstLogonCommands>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\ /v HideFileExt /t REG_DWORD /d 0 /f</CommandLine>
                        <Order>1</Order>
                        <Description>Show file extensions in Explorer</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKCU\Console /v QuickEdit /t REG_DWORD /d 1 /f</CommandLine>
                        <Order>2</Order>
                        <Description>Enable QuickEdit mode</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\ /v Start_ShowRun /t REG_DWORD /d 1 /f</CommandLine>
                        <Order>3</Order>
                        <Description>Show Run command in Start Menu</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\ /v StartMenuAdminTools /t REG_DWORD /d 1 /f</CommandLine>
                        <Order>4</Order>
                        <Description>Show Administrative Tools in Start Menu</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKLM\SYSTEM\CurrentControlSet\Control\Power\ /v HibernateFileSizePercent /t REG_DWORD /d 0 /f</CommandLine>
                        <Order>5</Order>
                        <Description>Zero Hibernation File</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKLM\SYSTEM\CurrentControlSet\Control\Power\ /v HibernateEnabled /t REG_DWORD /d 0 /f</CommandLine>
                        <Order>6</Order>
                        <Description>Disable Hibernation Mode</Description>
                    </SynchronousCommand>
                    
                    <!--
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>%SystemRoot%\System32\reg.exe ADD HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters\ /v DisabledComponents /t REG_DWORD /d 0xFF /f</CommandLine>
                        Order>7</Order>
                        <Description>Disable IPv6</Description>
                    </SynchronousCommand>
                    -->
                    
                    <!-- WITHOUT WINDOWS UPDATES -->
                    <!--
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>cmd.exe /c C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -File a:\enable-winrm.ps1</CommandLine>
                        <Description>Enable WinRM</Description>
                        <Order>8</Order>
                    </SynchronousCommand>
                    -->
                    <!-- END WITHOUT WINDOWS UPDATES -->
                    <!-- WITH WINDOWS UPDATES -->
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>cmd.exe /c a:\microsoft-updates.bat</CommandLine>
                        <Order>9</Order>
                        <Description>Enable Microsoft Updates</Description>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>cmd.exe /c C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -File a:\disable-screensaver.ps1</CommandLine>
                        <Description>Disable Screensaver</Description>
                        <Order>10</Order>
                        <RequiresUserInput>true</RequiresUserInput>
                    </SynchronousCommand>
                    
                    <SynchronousCommand wcm:action="add">
                        <CommandLine>cmd.exe /c C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -File a:\win-updates.ps1</CommandLine>
                        <Description>Install Windows Updates</Description>
                        <Order>11</Order>
                        <RequiresUserInput>true</RequiresUserInput>
                    </SynchronousCommand>
{other_commands}
                    
                    <!-- END WITH WINDOWS UPDATES -->
                </FirstLogonCommands>
                
                <OOBE>
                    <HideEULAPage>true</HideEULAPage>
                    <HideLocalAccountScreen>true</HideLocalAccountScreen>
                    <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
                    <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
                    <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
                    <NetworkLocation>Home</NetworkLocation>
                    <ProtectYourPC>1</ProtectYourPC>
                </OOBE>
                <UserAccounts>
                    <AdministratorPassword>
                        <Value>{admin_password}</Value>
                        <PlainText>true</PlainText>
                    </AdministratorPassword>
                </UserAccounts>

                <RegisteredOwner />
            </component>
        </settings>
        <settings pass="offlineServicing">
            <component name="Microsoft-Windows-LUA-Settings" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <EnableLUA>false</EnableLUA>
            </component>
        </settings>
        <cpi:offlineImage cpi:source="wim:c:/wim/install.wim#{operating_system}" xmlns:cpi="urn:schemas-microsoft-com:cpi" />
    </unattend>
    """
    #print(xml_data)

    return xml_data