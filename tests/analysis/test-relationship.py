from connpy import analysis

tree_file = 'dat/kali-freund-cell-file.csv'
rows = ( '1', '5', '7' )
cols = ( '3', '7', '5', '1', '1', '202' )

analysis.relationship( 'dat/relationship-matrix.csv', tree_file, rows = rows, \
	cols = cols )

analysis.relationship( 'dat/relationship-matrix-full.csv', tree_file )
