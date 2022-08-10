#!/usr/bin/env python3
import argparse
import pathlib
import sys
import os
import base64
import subprocess
import shlex

prog_head_template = """
using Jint;
using System;
using System.Text;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Runtime.InteropServices;

class Program
{
"""

prog_tail_template = """
}
"""

engine_template = """
    public static void Print(object s)
    {
        if (s == null)
            s = "null";
        Console.WriteLine(s.ToString());
    }

    public static void Sleep(object s)
    {
        if (s == null)
            s = 1;
        Thread.Sleep(Convert.ToInt32(s) * 1000);
    }

    private static Jint.Engine CreateEngine()
    {
        return new Engine()
            FUNCTION_CALLS
            .SetValue("sleep", new Action<object>(Sleep))
            .SetValue("print", new Action<object>(Print));
    }
"""

func_template = '.SetValue("ASSEMBLY_NAME", new Func<String, String>(ASSEMBLY_NAME_CAP))'

run_assembly_template = """
    [DllImport("shell32.dll", SetLastError = true)]
    static extern IntPtr CommandLineToArgvW(
        [MarshalAs(UnmanagedType.LPWStr)] string lpCmdLine, out int pNumArgs);

    static String runAssembly(String assemblyb64, String param) {
        int argc;
        var argv = CommandLineToArgvW(param, out argc);
        if (argv == IntPtr.Zero)
            throw new System.ComponentModel.Win32Exception();
        var args = new string[argc];
        try
        {
            for (var i = 0; i < args.Length; i++)
            {
                var p = Marshal.ReadIntPtr(argv, i * IntPtr.Size);
                args[i] = Marshal.PtrToStringUni(p);
            }
        }
        finally
        {
            Marshal.FreeHGlobal(argv);
        }
        byte[] lib_bytes = Convert.FromBase64String(assemblyb64);
        var assembly = Assembly.Load(lib_bytes);
        MethodInfo method = assembly.EntryPoint;
        var sw = new StringWriter();
        Console.SetOut(sw);
        Console.SetError(sw);

        object[] parameters = new[] { args };
        method.Invoke(null, parameters);
        Console.Out.Close();
        var sw1 = new StreamWriter(Console.OpenStandardOutput());
        sw1.AutoFlush = true;
        Console.SetOut(sw1);
        Console.SetError(sw1);
        return sw.ToString();
    }
"""
assembly_template = """
    static String ASSEMBLY_NAME_CAP(String param) {
        var lib = "BASE64_ASSEMBLY";
        return runAssembly(lib, param);
    }
"""

main_template = """
    static void Main(string[] args)
    {
        var source = @"
<SCRIPT>
        ";
        CreateEngine().Execute(source).GetCompletionValue();
    }
"""

def parse_args():
    parser = argparse.ArgumentParser(
        description='Build a .Net executable from a javascript script'
    )
    parser.add_argument(
        '--out', '-o', help='Exe file to write', default='out.cs', type=pathlib.Path
    )
    parser.add_argument(
        '--debug', '-d', help='Debug process', default=False, type=bool, nargs='?', const=True
    )
    parser.add_argument(
        '--infile', '-i', help='JS file to parse', required=True
    )
    options =  parser.parse_args()
    if os.path.exists(options.infile) is None:
        print(f"[-] {options.infile} does not exist")
        sys.exit()
    return options

if __name__ == "__main__":
    options = parse_args()

    with open(options.infile) as in_script:
        imports_list = False
        import_builder = list()
        script = ""
        for line in in_script:
            if line.startswith("/*Sources"):
                imports_list = True
            elif line.startswith("Sources*/"):
                imports_list = False
            elif line.startswith("#"):
                # Comment in script
                pass
            elif imports_list:
                entry = line.split('=')
                if len(entry) == 2:
                    import_builder.append((entry[0].strip(), entry[1].strip()))
            else:
                script += line

    if options.debug:
        print(f"[D] /----------SCRIPT -------------/")
        print(script)
        print(f"[D] /----------SCRIPT -------------/")
    # Patch the CSharp code to provide libraries to the user script
    func_list = ""
    lib_list = ""
    for assembly in import_builder:
        lib_tmp = ""
        func_tmp = func_template.replace("ASSEMBLY_NAME_CAP", assembly[0].capitalize())
        func_list += func_tmp.replace("ASSEMBLY_NAME", assembly[0])
        lib_tmp += assembly_template.replace("ASSEMBLY_NAME_CAP", assembly[0].capitalize())
        if os.path.exists(assembly[1]):
            with open(assembly[1], 'rb') as rf:
                lib_b64 = base64.b64encode(rf.read()).decode('ascii')
        else:
            print(f"[-] {assembly[0]}: {assembly[1]} not found!")
            sys.exit()
        if options.debug:
            print(f"[D] Loaded assembly {assembly[0]} b64 length: {len(lib_b64)}")
        lib_list += lib_tmp.replace("BASE64_ASSEMBLY", lib_b64)

    # Write the cs file
    cs_file = pathlib.Path(f"{os.path.join(options.out.parent, options.out.stem)}.cs")
    if options.debug:
        print(f"[D] Writing {cs_file}")
    with open(cs_file, 'w') as prog:
        prog.write(prog_head_template)
        prog.write(run_assembly_template)
        prog.write(lib_list)
        prog.write(engine_template.replace("FUNCTION_CALLS", func_list))
        prog.write(main_template.replace("<SCRIPT>", script.replace('"', '""')))
        prog.write(prog_tail_template)

    print("[+] Compiler Instructions:")
    compiler_cmd_line = f"mcs {cs_file} -out:{cs_file}.exe -r:Jint.dll"
    print(f"\t{compiler_cmd_line}")
    print("[+] Compiling")
    compiler = subprocess.run(shlex.split(compiler_cmd_line))
    if compiler.returncode != 0:
        print(f"[-] Compiler failed, check error messages")
        sys.exit()
    if options.debug:
        print(f"[D] Keeping {cs_file}")
    else:
        print(f"[+] Deleting {cs_file}")
        cs_file.unlink()
    merger_cmd_line = f"mono ILRepack.exe /out:{options.out} {cs_file}.exe Jint.dll"
    merger = subprocess.run(shlex.split(merger_cmd_line))
    if merger.returncode != 0:
        print(f"[-] Compiler failed, check error messages")
        sys.exit()
    if options.debug:
        print(f"[D] Keeping {cs_file}.exe")
    else:
        print(f"[+] Deleting {cs_file}.exe")
        pathlib.Path(f"{cs_file}.exe").unlink()
    if options.out.exists():
        print(f"[+] Compiled to {options.out}")
        print("[!] Winning, compiled and merged")
    else:
        print("[-] Errors in compilation")
