#========
# Pack / Clear / Unpack
#========
import os
import os.path as path
import shutil
import subprocess
import sys

class FileError( Exception ):
	pass

def _expand( target, base_dir ):
	target = path.join( base_dir, target )
	
	if not path.isdir( target ):
		raise( FileError( target + " is not a valid directory." ) )
	
	ls = os.listdir( target )
	is_sim = lambda x: x[ : 4 ] == 'sim-' and path.isdir( path.join( target, x ) )
	sim_dir = filter( is_sim, ls )
	sim_dir = sorted( [ path.join( target, s ) for s in sim_dir ] )
	data_dir = [ path.join( s, 'output' ) for s in sim_dir ]
	
	return sim_dir, data_dir

def pack( target = 'all', force = False, base_dir = '.' ):
	archive_file = 'output.tar.gz'
	
	if target == 'all':
		for i in range( 1000 ):
			# Convert 0 to '000', 1 to '001', etc.
			dir = format( i, '03' )
			if path.isdir( path.join( base_dir, dir ) ):
				pack( dir, force, base_dir )
			else:
				break
		return
	
	sim_dir, data_dir = _expand( target, base_dir )
	
	for sd, dd in zip( sim_dir, data_dir ):
		print "Packing " + dd + ":",
		sys.stdout.flush()
		
		if not path.isdir( dd ):
			print "Not a valid directory."
			continue
		
		cwd = os.getcwd()
		status = None
		
		try:
			# Checking for exceptions here only for the 'finally' block, where
			# the cwd is changed back to original. If a cleaner way is used to
			# handle the archive file, then this exception handling can be
			# removed.
			
			exists = path.exists( path.join( sd, archive_file ) )
			if not exists or force:
				os.chdir( sd )
				status = subprocess.call( ( 'tar', 'czf', archive_file, 'output' ) )
		except Exception:
			raise
		else:
			if status == None:
				print "Not done: " + archive_file + " exists.",
				print "Set force=True to force packing."
			elif status != 0:
				print "tar failed."
			else:
				if exists:
					print "Done. (overwrote " + archive_file + ")"
				else:
					print "Done."
		finally:
			os.chdir( cwd )

def clear( target, base_dir = '.' ):
	if target == 'all':
		for i in range( 1000 ):
			# Convert 0 to '000', 1 to '001', etc.
			dir = format( i, '03' )
			if path.isdir( path.join( base_dir, dir ) ):
				clear( dir, base_dir )
			else:
				break
		return
	
	sim_dir, data_dir = _expand( target, base_dir )
	
	for dd in data_dir:
		print "Deleting " + dd + ":",
		sys.stdout.flush()
		
		if not path.isdir( dd ):
			print "Not a valid directory."
			continue
		
		shutil.rmtree( dd )
		print "Done."

def unpack( target, force = False, base_dir = '.' ):
	archive_file = 'output.tar.gz'
	
	sim_dir, data_dir = _expand( target, base_dir )
	
	for sd, dd in zip( sim_dir, data_dir ):
		archive = path.join( sd, archive_file )
		
		print "Unpacking " + archive + ":",
		sys.stdout.flush()
		
		if not path.isfile( archive ):
			print "Not a valid file."
			continue
		
		cwd = os.getcwd()
		status = None
		
		try:
			# Checking for exceptions here only for the 'finally' block, where
			# the cwd is changed back to original. If a cleaner way is used to
			# handle the archive file, then this exception handling can be
			# removed.
			
			empty = not path.exists( dd ) or len( os.listdir( dd ) ) == 0
			if empty or force:
				os.chdir( sd )
				status = subprocess.call( ( 'tar', 'xzf', archive_file ) )
		except Exception:
			raise
		else:
			if status == None:
				print "Not done: " + dd + " exists and is not empty.",
				print "Set force=True to force packing."
			elif status != 0:
				print "tar failed."
			else:
				if not empty:
					print "Done. (wrote into non-empty directory " + dd + ")"
				else:
					print "Done."
		finally:
			os.chdir( cwd )

#
# Unit test
#
def _test_pack():
	from connpy import pack
	from connpy import analysis
	
	analysis.step_init( {
		"Preparing dir structure" : 1,
		"pack.pack() - 1st iteration" : 1,
		"pack.pack( force = True )" : 1,
		"pack.clear( 'all' )" : 1,
		"pack.pack() - 2nd iteration" : 1,
		"pack.unpack( i ) - 1st iteration" : 1,
		"pack.unpack( i ) - 2nd iteration" : 1,
		"pack.unpack( i, force = True )" : 1,
	} )
	
	print """Testing pack.

	Dir structure:

		000/
			sim-1/
				output/
			sim-2/
				output/
					f1
					f2
		001/
			sim-1/
			sim-2/
				output/
				output.tar.gz
			sim-3/
				output/
				output.tar.gz (No read/write permissions)
		003/
			sim-1/
				output/
	"""
	
	base_dir = 'tests/pack'
	
	import shutil
	import os
	import subprocess
	if analysis.step( "Preparing dir structure" ):
		os.chdir( 'tests' )
		if os.path.isdir( 'pack' ):
			shutil.rmtree( 'pack' )
		subprocess.call( ( 'tar', 'xzf', 'pack.tar.gz' ) )
		os.chdir( '..' )
		
		os.chmod( 'tests/pack/001/sim-3/output.tar.gz', 0000 )
	
	if analysis.step( "pack.pack() - 1st iteration" ):
		pack.pack( base_dir = base_dir )
	
	if analysis.step( "pack.pack( force = True )" ):
		pack.pack( force = True, base_dir = base_dir )
	
	if analysis.step( "pack.clear( 'all' )" ):
		pack.clear( 'all', base_dir = base_dir )
	
	if analysis.step( "pack.pack() - 2nd iteration" ):
		pack.pack( base_dir = base_dir )
	
	if analysis.step( "pack.unpack( i ) - 1st iteration" ):
		for i in ( '000', '001' ):
			pack.unpack( i, base_dir = base_dir )
	
	if analysis.step( "pack.unpack( i ) - 2nd iteration" ):
		for i in ( '000', '001' ):
			pack.unpack( i, base_dir = base_dir )
	
	if analysis.step( "pack.unpack( i, force = True )" ):
		for i in ( '000', '001' ):
			pack.unpack( i, force=True, base_dir = base_dir )

if __name__ == "__main__":
	_test_pack()
