simulator = 'genesis'

#========
# Compartment lengths
#========
import subprocess

def compartment_lengths( out_file, model_dir, script = 'length.g' ):
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
	
	#~ with open( tree_file ) as f:
		#~ reader = csv.reader( f, delimiter = '\t' )
		#~ for row in reader:
			#~ self = row[ 0 ]
			#~ parent = row[ 1 ]
			#~ if parent == 'none':
				#~ lineage[ self ] = []
			#~ else:
				#~ lineage[ self ] = lineage[ parent ] + [ parent ]
	
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
	
	header = [ '#Compartment' ]
	for i in reference:
		header.append( i )
	
	physical_matrix = [ header ]
	electrotonic_matrix = [ header ]
	
	for i in moving:
		physical_row = [ i ]
		electrotonic_row = [ i ]
		
		for j in reference:
			( physical, electrotonic ) = _distance_ij( lineage, length, i, j )
			physical_row.append( physical )
			electrotonic_row.append( electrotonic )
		
		physical_matrix.append( physical_row )
		electrotonic_matrix.append( electrotonic_row )
	
	with open( physical_out_file, "w" ) as f:
		writer = csv.writer( f, delimiter = '\t' )
		writer.writerows( physical_matrix )
	
	with open( electrotonic_out_file, "w" ) as f:
		writer = csv.writer( f, delimiter = '\t' )
		writer.writerows( electrotonic_matrix )

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
