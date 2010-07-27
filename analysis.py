import numpy

simulator = 'genesis'

#========
# Compartment lengths
#========
import subprocess

def compartment_lengths( out_file, model_dir, script = 'myg-length.g' ):
	print "[ compartment_lengths ]"
	print "	out_file :", out_file
	print "	model_dir :", model_dir
	print "	script :", script
	subprocess.call( ( simulator, script, model_dir, out_file ) )

#========
# Lineage
#========
import mypy
def _lineage( tree_file ):
	lineage = {}
	
	tf = mypy.load_csv( tree_file, delimiter = '\t' )
	for row in tf:
		self = row[ 0 ]
		parent = row[ 1 ]
		
		if parent == 'none':
			lineage[ self ] = []
		else:
			lineage[ self ] = lineage[ parent ] + [ parent ]
	
	return lineage

#========
# Relationship
#========
def _relationship_ij( lineage, a, b ):
	if a == b:
		return 1
	elif a in lineage[ b ]:
		return 2
	elif b in lineage[ a ]:
		return 0
	else:
		return -1

import csv
import mypy
def relationship( out_file, cell_file, rows = (), cols = () ):
	"""Generates a matrix which tells the relationship between one set of nodes
	(rows) and another (cols). Entries in the matrix can be one of:
		-1: separate branches
		1:  self
		0:  col is ancestor of row
		2:  col is descendant of row
	
	If 'rows' is not specified then all the nodes from the 'cell_file' are
	taken. Likewise for 'cols'.
	"""
	print "[ relationship ]"
	print "	out_file :", out_file
	print "	cell_file :", cell_file
	print "	rows :", rows
	print "	cols :", cols
	
	lineage = _lineage( cell_file )
	
	if rows == () or cols == ():
		cf = mypy.load_csv( cell_file, delimiter = '\t', comment = '#', cast = str )
		all_compts = [ c[ 0 ] for c in cf ]
	
	if isinstance( rows, str ):
		rows = ( rows, )
	elif rows == ():
		rows = all_compts
	
	if isinstance( cols, str ):
		cols = ( cols, )
	elif cols == ():
		cols = all_compts
	
	header = [ '#Compartment' ]
	for i in cols:
		header.append( i )
	
	matrix = [ header ]
	for i in rows:
		row = [ i ]
		for j in cols:
			row.append( _relationship_ij( lineage, i, j ) )
		
		matrix.append( row )
	
	with open( out_file, "w" ) as f:
		writer = csv.writer( f, delimiter = '\t' )
		writer.writerows( matrix )

#========
# Physical/Electrotonic distance
#========
def _distance_ij( lineage, length, a, b ):
	if a == b:
		return ( 0, 0 )
	
	path = set( lineage[ a ] ) ^ set( lineage[ b ] )
	
	if a in lineage[ b ]:
		path.remove( a )
	elif b in lineage[ a ]:
		path.remove( b )
	
	debug = not True
	if debug:
		print a, b, lineage[ a ], lineage[ b ], sorted( path )
	
	( pa, ea ) = length[ a ]
	( pb, eb ) = length[ b ]
	
	physical = ( pa + pb ) / 2
	electrotonic = ( ea + eb ) / 2
	
	for i in path:
		( p, e ) = length[ i ]
		physical = physical + p
		electrotonic = electrotonic + e
	
	return ( physical, electrotonic )

import csv
import mypy
def distance( physical_out_file, electrotonic_out_file, cell_file, length_file, reference = (), moving = () ):
	print "[ distance ]"
	print "	physical_out_file :", physical_out_file
	print "	electrotonic_out_file :", electrotonic_out_file
	print "	cell_file :", cell_file
	print "	length_file :", length_file
	print "	reference :", reference
	print "	moving :", moving
	
	length = {}
	lineage = _lineage( cell_file )
	
	if reference == () or moving == ():
		cf = mypy.load_csv( cell_file, delimiter = '\t', comment = '#', cast = str )
		all_compts = [ c[ 0 ] for c in cf ]
	
	lf = mypy.load_csv( length_file, delimiter = ' ', comment = '#', cast = str )
	for row in lf:
		self, physical, L, electrotonic = row
		length[ self ] = ( float( physical ), float( electrotonic ) )
	
	if isinstance( reference, str ):
		reference = ( reference, )
	elif reference == ():
		reference = all_compts
	
	if isinstance( moving, str ):
		moving = ( moving, )
	elif moving == ():
		moving = all_compts
	
	physical_matrix = [ ]
	electrotonic_matrix = [ ]
	
	for i in moving:
		physical_row = [ ]
		electrotonic_row = [ ]
		
		for j in reference:
			( physical, electrotonic ) = _distance_ij( lineage, length, i, j )
			physical_row.append( physical )
			electrotonic_row.append( electrotonic )
		
		physical_matrix.append( physical_row )
		electrotonic_matrix.append( electrotonic_row )
	
	header = [ '#Compartment' ]
	header.extend( reference )
	
	physical_matrix_labelled = physical_matrix
	physical_matrix_labelled = zip( *physical_matrix_labelled )
	physical_matrix_labelled.insert( 0, moving )
	physical_matrix_labelled = zip( *physical_matrix_labelled )
	physical_matrix_labelled.insert( 0, header )
	
	electrotonic_matrix_labelled = electrotonic_matrix
	electrotonic_matrix_labelled = zip( *electrotonic_matrix_labelled )
	electrotonic_matrix_labelled.insert( 0, moving )
	electrotonic_matrix_labelled = zip( *electrotonic_matrix_labelled )
	electrotonic_matrix_labelled.insert( 0, header )
	
	with open( physical_out_file, "w" ) as f:
		writer = csv.writer( f, delimiter = '\t' )
		writer.writerows( physical_matrix_labelled )
	
	with open( electrotonic_out_file, "w" ) as f:
		writer = csv.writer( f, delimiter = '\t' )
		writer.writerows( electrotonic_matrix_labelled )
	
	return ( numpy.array( physical_matrix ), numpy.array( electrotonic_matrix ) )

#========
# Summation distance
#========
import mypy
def _curve( file, stimulus_time ):
	mat = mypy.load_csv( file, delimiter = ' ', cast = float, comment = '#', skip_empty_entries = "ends" )
	
	curve = mypy.col( mat, ( 0, 1 ) )
	values = [
		value
		for ( time, value ) in curve
		if time >= stimulus_time
	]
	
	baseline = values[ 0 ]
	values = [ value - baseline for value in values ]
	
	return values

import csv
def summation_distance( out_file, single_file, pair_file, reference, moving, stimulus_time ):
	print "[ summation_distance ]"
	print "	out_file :", out_file
	print "	single_file :", single_file
	print "	pair_file :", pair_file
	print "	reference :", reference
	print "	moving :", moving
	print "	stimulus_time :", stimulus_time
	
	header = (
		'#Compartment',
		'aAmp', 'aArea',
		'bAmp', 'bArea',
		'pairAmp', 'pairArea',
		'ampLinearity', 'areaLinearity'
	)
	
	A = reference
	
	aCurve = _curve( single_file( A ), stimulus_time )
	aAmp = max( aCurve )
	aArea = sum( aCurve )
	data = [ header ]
	
	for B in moving:
		print "Reference:", A, "; Moving:", B,
		print "; Single file:", single_file( B ), "; Pair file:", pair_file( A, B )
		
		bCurve = _curve( single_file( B ), stimulus_time )
		pCurve = _curve( pair_file( A, B ), stimulus_time )
		
		#~ bAmp = max( bCurve )
		#~ bArea = sum( bCurve )
		#~ pAmp = max( pCurve )
		#~ pArea = sum( pCurve )
		#~ ampDistance = pAmp / ( aAmp + bAmp )
		#~ areaDistance = pArea / ( aArea + bArea )
		
		bAmp = max( bCurve )
		pAmp = max( pCurve )
		bArea = sum( bCurve )
		pArea = sum( pCurve )
		aPlusB = [ a + b for ( a, b ) in zip( aCurve, bCurve ) ]
		ampDistance = max( pCurve ) / max( aPlusB )
		areaDistance = pArea / ( aArea + bArea )
		
		data.append( (
			B,
			aAmp, aArea,
			bAmp, bArea,
			pAmp, pArea,
			ampDistance, areaDistance
		) )
	print
	
	writer = csv.writer( open( out_file, "w" ), delimiter = '\t' )
	writer.writerows( data )

#========
# EPSP characteristics
#========
import numpy
import pylab
import os
import os.path as path
import csv
import mypy
def epsp_characteristics(
	compartments,
	vm,
	ed_from_soma,
	pd_from_soma,
	t_min = None,
	t_max = None,
	out_dir = '.',
	soma_sub_dir = 'soma',
	local_sub_dir = 'local',
	stats_file = 'stats.txt',
	units = lambda v: `v * 1e3` + ' mV',
	all_epsps_image_file = 'EPSP.png',
	amplitude_vs_pd_from_soma_image_file = 'amplitude_vs_pd.png',
	amplitude_vs_ed_from_soma_image_file = 'amplitude_vs_ed.png',
	height_file = 'height.csv' ):
	"""
	Args:
		file_path: Path to file that needs to be loaded.
	
	Notes:
		If after skipping empty entries, a line is empty then it will be
	
	Returns:
		A 2-dimensional "array" containing a table read from the given file.
	"""
	for ( sub_dir, col ) in zip( ( soma_sub_dir, local_sub_dir ), ( 1, 2 ) ):
		directory = path.join( out_dir, sub_dir )
		
		mypy.require_dir( directory )
		
		stats_file_f = path.join( directory, stats_file )
		all_epsps_image_file_f = path.join( directory, all_epsps_image_file )
		amplitude_vs_pd_from_soma_image_file_f = path.join( directory, amplitude_vs_pd_from_soma_image_file )
		amplitude_vs_ed_from_soma_image_file_f = path.join( directory, amplitude_vs_ed_from_soma_image_file )
		height_file_f = path.join( directory, height_file )
		height = []
		
		pylab.figure()
		for c in compartments:
			print c,
			d = vm( c )
			
			if t_min != None and len( d ) > 0:
				d = d[ ( d[ :, 0 ] >= t_min ) ]
			if t_max != None and len( d ) > 0:
				d = d[ ( d[ :, 0 ] <= t_max ) ]
			
			pylab.plot( d[ :, 0 ], d[ :, col ] )
			
			vm_clip = d[ :, col ]
			height.append( max( vm_clip ) - vm_clip[ 0 ] )
		pylab.savefig( all_epsps_image_file_f )
		pylab.close()
		
		pylab.figure()
		pylab.plot( pd_from_soma, height, 'x' )
		pylab.savefig( amplitude_vs_pd_from_soma_image_file_f )
		pylab.close()
		
		pylab.figure()
		pylab.plot( ed_from_soma, height, 'x' )
		pylab.savefig( amplitude_vs_ed_from_soma_image_file_f )
		pylab.close()
		
		avg = numpy.average( height )
		std = numpy.std( height )
		cv = std / avg
		stats = \
			"Stats for EPSP height:" + "\n" + \
			"Minimum: " + units( min( height ) ) + "\n" + \
			"Maximum: " + units( max( height ) ) + "\n" + \
			"Average: " + units( avg ) + "\n" + \
			"Standard deviation: " + units( std ) + "\n" + \
			"Coefficient of variation (CV = std. dev. / avg.): " + `cv` + "\n"
		
		print "\n"
		print stats
		with open( stats_file_f, 'w' ) as f:
			f.write( stats )
		
		height_data = [ ( "#Compartment", "EPSP_height" ) ]
		height_data.extend( zip( compartments, height ) )
		with open( height_file_f, "w" ) as f:
			writer = csv.writer( f, delimiter = '\t' )
			writer.writerows( height_data )
