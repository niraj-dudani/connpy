#~ Not required since we are explicitly importing the modules below.
#~ __all__ = [ 'analysis', 'pack' ]

import analysis
import pack

simulator = 'genesis'

#========
# Controlling steps
#========
_step = {}

def step_init( steps ):
	global _step
	_step = steps

def step( step ):
	global _step
	print "#=============================================="
	print "# " + step
	print "#=============================================="
	return _step[ step ]

#========
# Controlling steps
#========
def file_list( flist ):
	print "#=============================================="
	print "# File list"
	print "#=============================================="
	for i in flist:
		print i[ 0 ], ":", i[ 1 ]

#========
# Runman
#========
import os, subprocess

def runman( sim_dir, model_dir, iteration_first = -1, iteration_last = -1 ):
	"""
	Equivalent to executing the following shell commands:
		export RUNMAN_PATH='runman'
		genesis runman/runman.g 000/sim-000 models/kali-freund
	If Ctrl-C is hit while GENESIS is running, the terminal does not
	behave well after that. Does not seem to happen if subprocess.call()
	is used to invoke some other program.
	"""
	print "[ runman ]"
	print "	sim_dir :", sim_dir
	print "	model_dir :", model_dir
	print "	iteration_first :", iteration_first
	print "	iteration_last :", iteration_last
	subprocess.call( ( simulator, 'runman.g', sim_dir, model_dir, `iteration_first`, `iteration_last` ) )
