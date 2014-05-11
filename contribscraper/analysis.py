from matplotlib import pyplot as PLT
from matplotlib import cm as CM
from geopy.geocoders import GoogleV3

import numpy as np

def generate_heatmap(x,y,fname):
	# x = y = np.linspace(-5, 5, 100)
	# print "x: " + str(type(x))
	# X, Y = np.meshgrid(x, y)
	# print "X: " + str(type(X))

	# x = X.ravel()
	# print "x: " + str(type(x))
	# y = Y.ravel()
	# gridsize=128
	heatmap, xedges, yedges = np.histogram2d(x, y, bins=(100,100))
	extent = [xedges[0],xedges[-1],yedges[0],yedges[-1]]

	PLT.clf()
	PLT.imshow(heatmap,extent=extent)
	PLT.savefig(fname)

	# if 'bins=None', then color of each hexagon corresponds directly to its count
	# 'C' is optional--it maps values to x-y coordinates; if 'C' is None (default) then 
	# the result is a pure 2D histogram 

	#PLT.hexbin(x, y, gridsize=gridsize, cmap=CM.jet, bins=None)
	#PLT.axis([x.min(), x.max(), y.min(), y.max()])

	#cb = PLT.colorbar()
	#cb.set_label('mean value')

def generate_map_bg(xmin,xmax,ymin,ymax):
	pass