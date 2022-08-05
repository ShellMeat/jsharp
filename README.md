# jsharp
Javascript to CSharp binary execution

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

# Special Functions
print - print to console

# Assemblies
Paths and definitions set in Sources header are added to the C# file as a base64 string and a function is created to call the assembly's entry point with with parameters. The console output of the command is returned as a string.

# TODOs
* Parse command line arguements so they are passed as a string array to the library
