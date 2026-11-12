"""Build the bundled official LuaJIT 2.0 in an ignored local cache."""
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,tarfile
W=Path(__file__).resolve().parent

def ensure_runtime():
 if sys.version_info<(3,12):raise SystemExit('Python 3.12+ required')
 if os.name=='nt':raise SystemExit('Windows: build bundled LuaJIT 2.0 with msvcbuild.bat, then pass --runtime ABSOLUTE_PATH/luajit.exe')
 archive=W/'LuaJIT-2.0-b83bcba.tar.gz'
 digest=hashlib.sha256(archive.read_bytes()).hexdigest()
 cache=W/'native_work'/'runtime';stamp=cache/'archive.sha256';runtime=cache/'luajit20/src/luajit'
 if runtime.is_file() and stamp.is_file() and stamp.read_text()==digest:
  version=subprocess.check_output([str(runtime),'-v'],stderr=subprocess.STDOUT)
  if version.startswith(b'LuaJIT 2.0.'):return runtime
 if cache.exists():shutil.rmtree(cache)
 cache.mkdir(parents=True)
 with tarfile.open(archive) as t:t.extractall(cache,filter='data')
 tmp=cache/'tmp';tmp.mkdir()
 with (cache/'build.log').open('wb') as log:
  subprocess.run(['make','-j4'],cwd=cache/'luajit20',env=os.environ|{'TMPDIR':str(tmp)},stdout=log,stderr=subprocess.STDOUT,check=True)
 version=subprocess.check_output([str(runtime),'-v'],stderr=subprocess.STDOUT)
 assert version.startswith(b'LuaJIT 2.0.'),version
 stamp.write_text(digest)
 return runtime
