#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import rbf.halton
from rbf.interpolant import RBFInterpolant
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import rbf.basis
import modest
import logging
import myplot.cm
from myplot.colorbar import pseudo_transparent_cmap
viridis_alpha = pseudo_transparent_cmap(myplot.cm.viridis,1.0)

logging.basicConfig(level=logging.DEBUG)

@modest.funtime
def grid_interp_data(u,pnts,x,y):
  if np.ma.isMaskedArray(u):
    pnts = pnts[~u.mask]
    u = u[~u.mask] 

  u = np.asarray(u)
  pnts = np.asarray(pnts)
  x = np.asarray(x)  
  y = np.asarray(y)
  
  xg,yg = np.meshgrid(x,y)
  xf,yf = xg.flatten(),yg.flatten()
  pnts_itp = np.array([xf,yf]).T
  I = RBFInterpolant(pnts,u,penalty=0.0,
                     order=1,basis=rbf.basis.phs1)
  uitp = I(pnts_itp)
  uitp = uitp.reshape((x.shape[0],y.shape[0]))                   
  return uitp
  
class InteractiveView:
  def __init__(self,data_sets,t,x,
               cmap=None,
               quiver_key_label=None,
               quiver_key_length=1.0,
               quiver_scale=10.0,
               quiver_key_pos=None,
               ylabel='displacement [m]',
               xlabel='time [years]'):
    ''' 

    interactively views vector valued data which is time and space 
    dependent
    
    Parameters
    ----------
      data : (Nt,Nx,3) array (can me masked)

      t : (Nt,) array

      x : (Nx,2) array
      
    '''                    
    fig1,ax1 = plt.subplots(3,1,sharex=True)
    fig2,ax2 = plt.subplots()
    self.highlight = True
    self.tidx,self.xidx = 0,0
    self.fig1,self.fig2 = fig1,fig2
    self.ax1,self.ax2 = ax1,ax2
    self.data_sets_original = data_sets
    self.data_sets_indices = range(len(data_sets))
    self.data_sets = [self.data_sets_original[i] for i in self.data_sets_indices]
    self.t = t
    self.x = x
    self.cmap = cmap
    self.quiver_scale = quiver_scale
    self.xlabel = xlabel
    self.ylabel = ylabel
    self.color_cycle = ['k','b','r','g','c','m','y']
    if quiver_key_pos is None:
      quiver_key_pos = (0.1,0.1)

    if quiver_key_label is None:   
      quiver_key_label = str(quiver_key_length) + ' [m]'

    self.quiver_key_pos = quiver_key_pos
    self.quiver_key_label = quiver_key_label
    self.quiver_key_length = quiver_key_length

    self._init_draw()

  def connect(self):
    self.fig1.canvas.mpl_connect('key_press_event',self._onkey)
    self.fig2.canvas.mpl_connect('key_press_event',self._onkey)
    self.fig2.canvas.mpl_connect('pick_event',self._onpick)


  def _init_draw(self):
    self.ax1[0].set_title('station %s' % self.xidx)
    self.ax1[2].set_xlabel(self.xlabel)
    self.ax1[0].set_ylabel(self.ylabel)
    self.ax1[1].set_ylabel(self.ylabel)
    self.ax1[2].set_ylabel(self.ylabel)
    # dont convert to exponential form
    self.ax1[0].get_xaxis().get_major_formatter().set_useOffset(False)
    self.ax1[1].get_xaxis().get_major_formatter().set_useOffset(False)
    self.ax1[2].get_xaxis().get_major_formatter().set_useOffset(False)
    self.ax2.set_title('time %g' % self.t[self.tidx])

    # highlighted point
    self.D = self.ax2.plot(self.x[self.xidx,0],
                           self.x[self.xidx,1],'ko',
                           markersize=20*self.highlight)[0]
    # pickable artists
    self.P = []
    for xi in self.x:
      self.P += self.ax2.plot(xi[0],xi[1],'.',
                              picker=10,
                              markersize=0)
    # quiver artists
    self.Q = []
    # line artists
    self.L1,self.L2,self.L3 = [],[],[]
    # image artist : self.I
    # scatter artist : self.S
    # quiver key : self.K
    for si in range(len(self.data_sets)):
      self.Q += [self.ax2.quiver(self.x[:,0],self.x[:,1],
                                 self.data_sets[si][self.tidx,:,0],
                                 self.data_sets[si][self.tidx,:,1],
                                 scale=self.quiver_scale,  
                                 color=self.color_cycle[si],zorder=2)]
      # time series instances
      self.L1 += self.ax1[0].plot(self.t,
                                  self.data_sets[si][:,self.xidx,0],
                                  color=self.color_cycle[si])
      self.L2 += self.ax1[1].plot(self.t,
                                  self.data_sets[si][:,self.xidx,1],
                                  color=self.color_cycle[si])
      self.L3 += self.ax1[2].plot(self.t,
                                  self.data_sets[si][:,self.xidx,2],
                                  color=self.color_cycle[si])
      # quiver key
      if si == 0:
        self.K = self.ax2.quiverkey(self.Q[si],
                                    self.quiver_key_pos[0],
                                    self.quiver_key_pos[1],
                                    self.quiver_key_length,
                                    self.quiver_key_label,zorder=2)

      if si == 0:
        # interpolate z value for first data set
        xlim = self.ax2.get_xlim()
        ylim = self.ax2.get_xlim()
        self.x_itp = [np.linspace(xlim[0],xlim[1],100),
                      np.linspace(ylim[0],ylim[1],100)]
        data_itp = grid_interp_data(self.data_sets[si][self.tidx,:,2],
                                    self.x,
                                    self.x_itp[0],self.x_itp[1])
        vmin = data_itp.min()
        self.I = self.ax2.imshow(data_itp,extent=(xlim+ylim),
                                 interpolation='none',
                                 origin='lower',
                                 vmin=data_itp.min(),
                                 vmax=data_itp.max(),
                                 cmap=self.cmap,zorder=0)
        self.I.set_clim((data_itp.min(),data_itp.max()))

        self.cbar = self.fig2.colorbar(self.I)  
        self.cbar.set_clim((data_itp.min(),data_itp.max()))

      if si == 1:  
        ylim = self.ax2.get_ylim()  
        xlim = self.ax2.get_xlim()  
        self.sm = ScalarMappable(norm=self.cbar.norm,cmap=self.cmap)
        # use scatter points to show z for second data set 
        colors = self.sm.to_rgba(self.data_sets[si][self.tidx,:,2])
        self.S = self.ax2.scatter(self.x[:,0],self.x[:,1],
                                  c=colors,
                                  s=200,zorder=1,
                                  edgecolor=self.color_cycle[si])
        self.ax2.set_ylim(ylim)
        self.ax2.set_xlim(xlim)
      
    self.fig1.tight_layout()
    self.fig2.tight_layout()
    self.fig1.canvas.draw()
    self.fig2.canvas.draw()


  def _draw(self):
    self.tidx = self.tidx%self.data_sets[0].shape[0]
    self.xidx = self.xidx%self.data_sets[0].shape[1]

    self.ax1[0].set_title('station %s' % self.xidx)
    self.ax2.set_title('time %g' % self.t[self.tidx])

    self.D.set_data(self.x[self.xidx,0],
                    self.x[self.xidx,1])
    self.D.set_markersize(20*self.highlight)

    for si in range(len(self.data_sets)):
      self.Q[si].set_UVC(self.data_sets[si][self.tidx,:,0],
                         self.data_sets[si][self.tidx,:,1])
      self.L1[si].set_data(self.t,
                           self.data_sets[si][:,self.xidx,0])
      self.L2[si].set_data(self.t,
                           self.data_sets[si][:,self.xidx,1])
      self.L3[si].set_data(self.t,
                           self.data_sets[si][:,self.xidx,2])

      if si == 0:
        data_itp = grid_interp_data(self.data_sets[si][self.tidx,:,2],
                                    self.x,
                                    self.x_itp[0],self.x_itp[1])
        self.I.set_data(data_itp)
        self.I.set_clim((data_itp.min(),data_itp.max()))
        self.cbar.set_clim((data_itp.min(),data_itp.max()))

      if si == 1:
        colors = self.sm.to_rgba(self.data_sets[si][self.tidx,:,2])
        self.S.set_facecolors(colors)

    self.ax1[0].relim()
    self.ax1[1].relim()
    self.ax1[2].relim()
    self.ax1[0].autoscale_view()
    self.ax1[1].autoscale_view()
    self.ax1[2].autoscale_view()

    self.fig1.canvas.draw()
    self.fig2.canvas.draw()


  def _onpick(self,event):
    for i,v in enumerate(self.P):
      if event.artist == v:
        self.xidx = i
        break

    self._draw()    


  def _onkey(self,event):
    print(event.key)
    if event.key == 'right':
      self.tidx += 1

    elif event.key == 'ctrl+right':
      self.tidx += 10

    elif event.key == 'alt+right':
      self.tidx += 100

    elif event.key == 'left':
      self.tidx -= 1

    elif event.key == 'ctrl+left':
      self.tidx -= 10

    elif event.key == 'alt+left':
      self.tidx -= 100

    elif event.key == 'up':
      self.xidx += 1

    elif event.key == 'ctrl+up':
      self.xidx += 10

    elif event.key == 'alt+up':
      self.xidx += 100

    elif event.key == 'down':
      self.xidx -= 1

    elif event.key == 'ctrl+down':
      self.xidx -= 10

    elif event.key == 'alt+down':
      self.xidx -= 100

    elif event.key == 'c':
      self.highlight = not self.highlight

    elif event.key == 'r':
      # roll order of data arrays 
      self.data_sets_indices = np.roll(self.data_sets_indices,1)
      print(self.data_sets_indices)
      self.data_sets = [self.data_sets_original[i] for i in self.data_sets_indices]

    else:
      # do nothing
      return

    self._draw()    
    
Nt = 100
Nx = 20
t = 2010 + np.linspace(0.0,1.0,Nt)
x = rbf.halton.halton(Nx,2)
data = (np.cos(6*t[:,None,None]) *
        np.sin(10*x[:,0])[None,:,None] *
        np.cos(10*x[:,1])[None,:,None])
data = data.repeat(3,axis=2)
data[data > 0.5] = np.nan
data = np.ma.masked_array(data,mask=np.isnan(data))
a1 = InteractiveView([data,data+np.random.normal(0.0,1.1,data.shape),-data],
                    t,x,cmap=viridis_alpha)
a2 = InteractiveView([data],
                     t,x,cmap=viridis_alpha)
a1.connect()
a2.connect()
plt.show()
quit()
#fig,axs = plt.subplots(1,2)
#_static_view(data,t,x,0,0,axs[0],axs[1])
#plt.show()
#quit()

class MatrixViewer:
  def __init__(self,M):
    self.ridx = 0
    self.cidx = 0
    fig,axs = plt.subplots(1,2)
    axs[0].plot(M[self.ridx,:])
    axs[1].plot(M[:,self.cidx])
    self.fig = fig
    self.axs = axs
    self.M = M

  def connect(self):
    self.fig.canvas.mpl_connect('key_press_event',self.onkey)
    self.fig.canvas.mpl_connect('pick_event',self.onpick)
 
  def draw(self):
    self.axs[0].cla()
    self.axs[1].cla()
    self.axs[0].plot(self.M[self.ridx,:],picker=10)
    self.axs[1].plot(self.M[:,self.cidx],picker=10)
    self.fig.canvas.draw()
    
  def onpick(self,event):
    print('foo!!!')

  def onkey(self,event):
    if event.key == 'right':
      self.cidx += 1
      self.draw()    
    elif event.key == 'left':
      self.cidx -= 1
      self.draw()    
    elif event.key == 'up':
      self.ridx += 1
      self.draw()    
    elif event.key == 'down':
      self.ridx -= 1
      self.draw()    
    
        
class LineBuilder:
    def __init__(self, line):
        self.line = line
        self.xs = list(line.get_xdata())
        self.ys = list(line.get_ydata())
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        print('click', event)
        if event.inaxes!=self.line.axes: return
        self.xs.append(event.xdata)
        self.ys.append(event.ydata)
        self.line.set_data(self.xs, self.ys)
        self.line.figure.canvas.draw()

M = np.random.random((20,10))
A = MatrixViewer(M)
A.connect()
#fig = plt.figure()
#ax = fig.add_subplot(111)
#a#x.set_title('click to build line segments')
#line, = ax.plot([0], [0])  # empty line
#linebuilder = LineBuilder(line)

plt.show()
