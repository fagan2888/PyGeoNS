#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import rbf.halton
import rbf.basis
import modest
import gps.plot
from pygeons.view import interactive_viewer

t = np.linspace(0,1,100) # form observation times
x = np.random.normal(0.0,1.0,(20,2)) # form observation positions
x[:,0] += -84.0
x[:,1] += 43.0

fig,ax = plt.subplots()
bm = gps.plot.create_default_basemap(x[:,1],x[:,0])
bm.drawstates(ax=ax)
bm.drawcountries(ax=ax)
bm.drawcoastlines(ax=ax)
bm.drawparallels(np.arange(30,90),ax=ax)
bm.drawmeridians(np.arange(-100,-60),ax=ax)
#help(bm.drawmeridians)
pos_x,pos_y = bm(x[:,0],x[:,1])
pos = np.array([pos_x,pos_y]).T
x = pos

u1,v1,z1 = np.cumsum(np.random.normal(0.0,0.5,(3,100,20)),axis=1)                   
u2,v2,z2 = np.cumsum(np.random.normal(0.0,0.5,(3,100,20)),axis=1)                   
su = 1.0 + 0*u1
sv = 1.0 + 0*u1
sz = 1.0 + 0*u1

interactive_viewer(t,x,u=[u1,u2],v=[v1,v2],z=[z1,z2],su=[su,su],sv=[sv,sv],
                   map_ax=ax) 
#network_viewer(t,x,u=[u1],v=[v1],z=[z1],su=[su],sv=[sv],sz=[sz],
#               map_ax=ax) 
#network_viewer(t,pos,u=[u1,u2],v=[v1,v2],z=[z1,z2],map_ax=ax,quiver_scale=0.00001) 
