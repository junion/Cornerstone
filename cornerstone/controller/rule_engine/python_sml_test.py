import sys
#sys.path.append('.')
import soar.Python_sml_ClientInterface as sml

k = sml.Kernel.CreateKernelInNewThread()
a = k.CreateAgent('soar')
print a.ExecuteCommandLine('echo hello world!!!')

