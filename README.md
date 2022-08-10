# Jsharp
Javascript to CSharp binary execution

# Usage
``` 
usage: build.py [-h] [--out OUT] [--debug [DEBUG]] --infile INFILE

Build a .Net executable from a javascript script

options:
  -h, --help            show this help message and exit
  --out OUT, -o OUT     Exe file to write
  --debug [DEBUG], -d [DEBUG]
                        Debug process
  --infile INFILE, -i INFILE
                        JS file to parse
```

# Sample Script
``` javascript
/*Sources
rubeus = /path/to/rubeus.exe
Sources*/
var klist = rubeus("klist");
if (klist.indexOf("krbtgt") > 0) {
    print("Found krbtgt ticket!");
}
```

Javascript support to this standard: https://262.ecma-international.org/5.1/

# Special Functions
print(str s) - print to console
sleep(int n) - Sleep for n seconds

# Assemblies
Paths and definitions set in Sources header are added to the C# file as a base64 string and a function is created to call the assembly's entry point with with parameters. The console output of the command is returned as a string.

# External References
https://github.com/gluck/il-repack   -- Merge all Jint.dll into the exe for a single file deployment
https://github.com/sebastienros/jint -- Using Version 2.11.58
