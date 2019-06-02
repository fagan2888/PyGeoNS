''' 
This module contains functions which parse a text file for a single 
station and return a dictionary with the following entries. 

  * id : 4-character station name
  * longitude : 
  * latitude :
  * time : array of observation times in Modified Julian Date (MJD)
  * east : array of easting observations in meters**p * days**q
  * north :               '' 
  * vertical :            ''
  * east_std_dev : standard deviation in meters**p * days**q
  * north_std_dev :           ''
  * vertical_std_dev :        ''
  * space_exponent : the exponent for the spatial unit 
  * time_exponent : the exponent for the temporal unit

The parser function should be able to fill in any required information 
that is not in the text file.

'''
import numpy as np
import logging
from pygeons.mjd import mjd
logger = logging.getLogger(__name__)  

def _get_line_with(sub,master):
  ''' 
  gets line with the first occurrence of sub
  '''
  idx = master.find(sub)
  if idx == -1:
    raise ValueError('Cannot find substring "%s"' % sub)

  line_start = master.rfind('\n',0,idx)
  if line_start == -1:
    # this is if sub is on the first line
    line_start = 0
  else:
    line_start += 1

  line_end = master.find('\n',line_start)
  if line_end == -1:
    # this is if sub is on the last line
    line_end = len(master)

  return master[line_start:line_end]


def _get_field(field,master,delim=':'):
  ''' 
  finds the first line containing *field*, splits the line by *delim*, 
  then returns the list element which follows the one containing 
  *field*. Any surrounding whitespace is removed from the value.
  '''
  if delim in field:
    raise ValueError('Field "%s" contains the delimiter "%s"' % (field,delim))

  # first line containing field
  line = _get_line_with(field,master)
  # split by delimiter
  lst = line.split(delim)
  # find the index containing field
  for i,j in enumerate(lst): 
    if field in j: 
      field_idx = i
      break

  # entry after the one containing field
  if (field_idx + 1) >= len(lst):
    raise ValueError(
      'No value associated with the field "%s". Make sure the '
      'correct delimiter is being used' % field)    

  out = lst[field_idx + 1]
  # remove white space
  out = out.strip()
  return out


def parse_csv(file_str):
  ''' 
  Reads data from a single PyGeoNS csv file
  '''
  fmt = '%Y-%m-%d'
  delim = ','

  def date_conv(date_bytes): 
    # return a float, rather than an integer, to be consistent with 
    # the other data types
    date_str = date_bytes.decode()
    return float(mjd(date_str,fmt))

  # make everything lowercase so that field searches are not case 
  # sensitive
  file_str = file_str.lower()
  id = _get_field('4-character id',file_str,delim=delim)
  logger.debug('reading csv data for station %s' % id.upper()) 

  lon_str = _get_field('longitude',file_str,delim=delim)
  lon,dir = lon_str.split()
  lon = float(lon)
  if dir.upper() == 'W':
    # make sure longitude component is east
    lon *= -1.0   
  
  lat_str = _get_field('latitude',file_str,delim=delim)
  lat,dir = lat_str.split()
  lat = float(lat)
  if dir.upper() == 'S':
    # make sure latitude component is north
    lat *= -1.0   

  units = _get_field('units',file_str,delim=delim)
  space_exponent = units.split()[0].split('**')[1]
  time_exponent = units.split()[1].split('**')[1]
  start = _get_field('begin date',file_str,delim=delim)
  # index of the first character in the data block
  data_start_idx = file_str.rfind(start)
  data = file_str[data_start_idx:]
  data = np.genfromtxt(data.split('\n'),
                       converters={0:date_conv},
                       delimiter=delim,
                       usecols=(0,1,2,3,4,5,6))
  # make sure that the data set is a two-dimensional array
  data = data.reshape((-1,7))
  output = {}
  output['id'] = id.upper()
  output['longitude'] = np.float(lon)
  output['latitude'] = np.float(lat)
  output['time'] = data[:,0].astype(int)
  output['north'] = data[:,1].astype(float)
  output['east'] = data[:,2].astype(float)
  output['vertical'] = data[:,3].astype(float)
  output['north_std_dev'] = data[:,4].astype(float)
  output['east_std_dev'] = data[:,5].astype(float)
  output['vertical_std_dev'] = data[:,6].astype(float)
  output['time_exponent'] = int(time_exponent)
  output['space_exponent'] = int(space_exponent)
  return output 


def parse_pbocsv(file_str):
  ''' 
  Reads data from a single PBO csv file
  '''
  fmt = '%Y-%m-%d'
  delim = ','

  def date_conv(date_bytes): 
    date_str = date_bytes.decode()
    return float(mjd(date_str,fmt))

  # make everything lowercase so that field searches are not case 
  # sensitive
  file_str = file_str.lower()
  id = _get_field('4-character id',file_str,delim=delim)
  logger.debug('reading csv data for station %s' % id.upper()) 

  start = _get_field('begin date',file_str,delim=delim)
  pos = _get_line_with('reference position',file_str)
  lon,lat = pos.split()[5],pos.split()[2]

  data_start_idx = file_str.rfind(start)
  data = file_str[data_start_idx:]
  data = np.genfromtxt(data.split('\n'),
                       converters={0:date_conv},
                       delimiter=delim,
                       usecols=(0,1,2,3,4,5,6))
  output = {}
  output['id'] = id.upper()
  output['longitude'] = np.float(lon)
  output['latitude'] = np.float(lat)
  output['time'] = data[:,0].astype(int)
  # comvert from millimeters to meters  
  output['north'] = 0.001*data[:,1].astype(float)
  output['east'] = 0.001*data[:,2].astype(float)
  output['vertical'] = 0.001*data[:,3].astype(float)
  output['north_std_dev'] = 0.001*data[:,4].astype(float)
  output['east_std_dev'] = 0.001*data[:,5].astype(float)
  output['vertical_std_dev'] = 0.001*data[:,6].astype(float)
  # indicate that the data are in units of meters
  output['time_exponent'] = 0  
  output['space_exponent'] = 1
  return output 


def parse_tdecsv(file_str):
  ''' 
  Reads data from a single data file which has the format used by the 
  SCEC Geodetic Transient Detection Validation Exercise
  '''
  fmt = '%Y-%m-%d'
  delim = ','

  def date_conv(date_bytes): 
    date_str = date_bytes.decode()
    return float(mjd(date_str,fmt))

  # make everything lowercase so that field searches are not case 
  # sensitive
  file_str = file_str.strip()
  file_str = file_str.lower()
  line_one = file_str[:file_str.find('\n')]
  id = line_one.split(',')[0].split()[1]
  lat = line_one.split(',')[1]
  lon = line_one.split(',')[2]
  data_start_idx = file_str.find('\n') + 1

  logger.debug('reading csv data for station %s' % id.upper()) 
  data = file_str[data_start_idx:]
  data = np.genfromtxt(data.split('\n'),
                       converters={0:date_conv},
                       delimiter=delim,
                       usecols=(0,1,2,3))
  output = {}
  output['id'] = id.upper()
  output['longitude'] = np.float(lon)
  output['latitude'] = np.float(lat)
  output['time'] = data[:,0].astype(int)
  # comvert from millimeters to meters  
  output['north'] = 0.001*data[:,2].astype(float)
  output['east'] = 0.001*data[:,1].astype(float)
  output['vertical'] = 0.001*data[:,3].astype(float)
  output['north_std_dev'] = 0.001*np.ones(len(data[:,0]))
  output['east_std_dev'] = 0.001*np.ones(len(data[:,0]))
  output['vertical_std_dev'] = 0.001*np.ones(len(data[:,0]))
  # indicate that the data are in units of meters
  output['time_exponent'] = 0  
  output['space_exponent'] = 1
  return output 


def parse_pbopos(file_str):
  ''' 
  Reads data from a single PBO pos file
  '''
  fmt = '%Y%m%d'

  def date_conv(date_bytes): 
    date_str = date_bytes.decode()
    return float(mjd(date_str,fmt))

  # make everything lowercase so that field searches are not case 
  # sensitive
  file_str = file_str.lower()
  id = _get_field('4-character id',file_str,delim=':')
  logger.debug('reading pos data for station %s' % id.upper()) 

  start = _get_field('first epoch',file_str,delim=':')
  pos = _get_field('neu reference position',file_str,delim=':')
  lon,lat = pos.split()[1],pos.split()[0]

  data_start_idx = file_str.rfind(start)
  data = file_str[data_start_idx:]
  data = np.genfromtxt(data.split('\n'),
                       converters={0:date_conv},
                       usecols=(0,15,16,17,18,19,20))
  output = {}
  output['id'] = id.upper()
  output['longitude'] = np.float(lon)
  output['latitude'] = np.float(lat)
  output['time'] = data[:,0].astype(int)
  output['north'] = data[:,1].astype(float)
  output['east'] = data[:,2].astype(float)
  output['vertical'] = data[:,3].astype(float)
  output['north_std_dev'] = data[:,4].astype(float)
  output['east_std_dev'] = data[:,5].astype(float)
  output['vertical_std_dev'] = data[:,6].astype(float)
  # indicate that the units are in meters
  output['time_exponent'] = 0
  output['space_exponent'] = 1
  return output 
  
# dictionary of all parsers defined in this module
PARSER_DICT = {'csv':parse_csv,
               'pbocsv':parse_pbocsv,
               'tdecsv':parse_tdecsv,
               'pbopos':parse_pbopos}


