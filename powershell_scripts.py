# Python script that includes powershell commands to be written to file during setup of windows
# Powershell scripts will be run on install
# DO NOT USE SINGLE QUOTES ' AS THEY WOULD NEED TO BE ESCAPED FOR ECHO TO WORK CORRECTLY

# Define function that contains powershell script to install google chrome
def install_chrome():
    # Script save name
    script_name = "install_chrome.ps1"
    # Command to install google chrome
    command = """# Modern websites require TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$LocalTempDir = $env:TEMP
$ChromeInstaller = "ChromeInstaller.exe"
(new-object System.Net.WebClient).DownloadFile("http://dl.google.com/chrome/install/375.126/chrome_installer.exe", "$LocalTempDir\$ChromeInstaller")
& "$LocalTempDir\$ChromeInstaller" /silent /install
$Process2Monitor = "ChromeInstaller"
Do {
    $ProcessesFound = Get-Process | ?{$Process2Monitor -contains $_.Name} | Select-Object -ExpandProperty Name
    If ($ProcessesFound) {
        Start-Sleep -Seconds 2
    } else {
        rm "$LocalTempDir\$ChromeInstaller" -ErrorAction SilentlyContinue
    }
} Until (!$ProcessesFound)"""
    
    return command, script_name
    

# Define function that contains powershell script to install notepad++
def install_notepad():
    # Script save name
    script_name = "install_notepad.ps1"
    # Command to install notepad++

    command = """# Modern websites require TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$BaseUri = "https://notepad-plus-plus.org"
$BasePage = Invoke-WebRequest -Uri $BaseUri -UseBasicParsing
$ChildPath = $BasePage.Links | Where-Object { $_.outerHTML -like "*Current Version*" } | Select-Object -ExpandProperty href
# Now let's go to the latest version's page and find the installer
$DownloadPageUri = $BaseUri + $ChildPath
$DownloadPage = Invoke-WebRequest -Uri $DownloadPageUri -UseBasicParsing
# Determine bit-ness of O/S and download accordingly
$DownloadUrl = $DownloadPage.Links | Where-Object { $_.outerHTML -like "*npp.*.Installer.x64.exe*" } | Select-Object -ExpandProperty href -Unique
$DownloadUrl = $DownloadUrl.split()
$DownloadUrl = $DownloadUrl[0]
Invoke-WebRequest -Uri $DownloadUrl -OutFile "$env:TEMP\$( Split-Path -Path $DownloadUrl -Leaf )" | Out-Null
Start-Process -FilePath "$env:TEMP\$( Split-Path -Path $DownloadUrl -Leaf )" -ArgumentList "/S" -Wait"""

    return command, script_name
    
    
# Define function that contains powershell script to install 7zip
def install_7zip():
    # Script save name
    script_name = "install_7zip.ps1"
    # Command to install 7zip
    command = """# Modern websites require TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$dlurl = "https://7-zip.org/" + (Invoke-WebRequest -UseBasicParsing -Uri "https://7-zip.org/" | Select-Object -ExpandProperty Links | Where-Object {($_.outerHTML -match "Download")-and ($_.href -like "a/*") -and ($_.href -like "*-x64.exe")} | Select-Object -First 1 | Select-Object -ExpandProperty href)
# modified to work without IE
# above code from: https://perplexity.nl/windows-powershell/installing-or-updating-7-zip-using-powershell/
$installerPath = Join-Path $env:TEMP (Split-Path $dlurl -Leaf)
Invoke-WebRequest $dlurl -OutFile $installerPath
Start-Process -FilePath $installerPath -Args "/S" -Verb RunAs -Wait
Remove-Item $installerPath"""

    return command, script_name
    

# Define function that contains powershell script to install python
def install_python():
    # Script save name
    script_name = "install_python.ps1"
    # Command to install the latest python version
    command = """# Modern websites require TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$latest_url = (Invoke-RestMethod "https://www.python.org/downloads/") -match "\\bhref=(?<url>.+?\.exe)"
$latest_url = $Matches.url
$latest_url = $latest_url.replace("`"", "")

$latest_version = (Invoke-RestMethod "https://www.python.org/downloads/") -match "Download Python (?<version>\d+\.\d+\.\d+)"
$latest_version = $Matches.version

Write-Host "Installing Python version:" $latest_version
$installerPath = Join-Path $env:TEMP (Split-Path $latest_url -Leaf)

Invoke-WebRequest $latest_url -OutFile $installerPath
Start-Process -FilePath $installerPath -Args "/S" -Verb RunAs -Wait
Remove-Item $installerPath"""
    
    return command, script_name


# Define a function to get all function definitions from this file.
# Returns a list of function names without the install_ in front of it
# This function should come last
def get_functions(dictionary = dict(locals())):
    defined_functions = []
    for key, value in dictionary.items():
        if "function" in str(value):
            if "get_functions" not in str(key):
                defined_functions.append(key)

    return defined_functions